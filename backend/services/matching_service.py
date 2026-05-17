"""
Aspire English Hub - Smart Matching Service
=============================================
Queue-based matchmaking ensuring same-batch students never connect.
"""

from config import settings
from supabase import create_client
from fastapi import HTTPException
import logging
from datetime import datetime, timezone
from typing import Optional, Dict

logger = logging.getLogger(__name__)
supabase_admin = create_client(settings.supabase_url, settings.supabase_service_key) if settings.supabase_service_key else None


class MatchingService:
    def __init__(self):
        self._active_searches: Dict[str, dict] = {}

    async def join_queue(self, user_id: str) -> dict:
        profile = supabase_admin.table("profiles").select(
            "id, batch_id, branch_id, is_banned"
        ).eq("id", user_id).single().execute()

        if not profile.data:
            raise HTTPException(status_code=404, detail="Profile not found")
        if profile.data.get("is_banned"):
            raise HTTPException(status_code=403, detail="Account suspended")
        if not profile.data.get("batch_id"):
            raise HTTPException(status_code=400, detail="Must be assigned to a batch first")

        existing = supabase_admin.table("call_queue").select("id, status").eq(
            "user_id", user_id).eq("status", "waiting").execute()
        if existing.data:
            return {"status": "already_waiting", "queue_id": existing.data[0]["id"]}

        queue_entry = supabase_admin.table("call_queue").insert({
            "user_id": user_id,
            "batch_id": profile.data["batch_id"],
            "branch_id": profile.data["branch_id"],
            "status": "waiting"
        }).execute()

        if not queue_entry.data:
            raise HTTPException(status_code=500, detail="Failed to join queue")

        self._active_searches[user_id] = {
            "queue_id": queue_entry.data[0]["id"],
            "batch_id": profile.data["batch_id"]
        }

        match = await self.find_match(user_id, profile.data["batch_id"])
        if match:
            return {"status": "matched", "queue_id": queue_entry.data[0]["id"],
                    "matched_user_id": match["matched_user_id"], "call_id": match.get("call_id")}

        return {"status": "waiting", "queue_id": queue_entry.data[0]["id"], "position": 1}

    async def find_match(self, user_id: str, batch_id: str) -> Optional[dict]:
        """Find partner from DIFFERENT batch only."""
        result = supabase_admin.rpc("find_match", {
            "p_user_id": user_id, "p_batch_id": batch_id
        }).execute()

        if result.data and len(result.data) > 0:
            matched_user_id = result.data[0]["matched_user_id"]
            supabase_admin.table("call_queue").update({
                "status": "matched", "matched_at": datetime.now(timezone.utc).isoformat()
            }).eq("user_id", user_id).eq("status", "waiting").execute()

            call = supabase_admin.table("active_calls").insert({
                "caller_id": user_id, "receiver_id": matched_user_id,
                "call_type": "peer", "status": "connecting"
            }).execute()

            self._active_searches.pop(user_id, None)
            self._active_searches.pop(matched_user_id, None)
            return {"matched_user_id": matched_user_id, "call_id": call.data[0]["id"] if call.data else None}
        return None

    async def leave_queue(self, user_id: str) -> dict:
        supabase_admin.table("call_queue").update({"status": "cancelled"}).eq(
            "user_id", user_id).eq("status", "waiting").execute()
        self._active_searches.pop(user_id, None)
        return {"status": "cancelled"}

    async def get_queue_status(self, user_id: str) -> dict:
        result = supabase_admin.table("call_queue").select("*").eq(
            "user_id", user_id).in_("status", ["waiting", "matched"]).order(
            "joined_at", desc=True).limit(1).execute()
        if result.data:
            return {"status": result.data[0]["status"], "queue_id": result.data[0]["id"]}
        return {"status": "not_in_queue"}

    async def get_online_count(self) -> dict:
        online = supabase_admin.table("profiles").select("id", count="exact").eq("is_online", True).execute()
        in_queue = supabase_admin.table("call_queue").select("id", count="exact").eq("status", "waiting").execute()
        return {"online_count": online.count or 0, "queue_count": in_queue.count or 0}


matching_service = MatchingService()
