"""
Aspire English Hub - Call Service
==================================
Manages voice calls, call history, and call analytics.
"""

from config import settings
from supabase import create_client
from fastapi import HTTPException
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
supabase_admin = create_client(settings.supabase_url, settings.supabase_service_key) if settings.supabase_service_key else None


class CallService:
    async def start_call(self, caller_id: str, receiver_id: str, call_type: str = "peer") -> dict:
        result = supabase_admin.table("active_calls").insert({
            "caller_id": caller_id, "receiver_id": receiver_id,
            "call_type": call_type, "status": "connecting"
        }).execute()
        if result.data:
            return result.data[0]
        raise HTTPException(status_code=500, detail="Failed to start call")

    async def connect_call(self, call_id: str) -> dict:
        result = supabase_admin.table("active_calls").update({
            "status": "active", "connected_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", call_id).execute()
        return result.data[0] if result.data else {}

    async def end_call(self, call_id: str, user_id: str) -> dict:
        call = supabase_admin.table("active_calls").select("*").eq("id", call_id).single().execute()
        if not call.data:
            raise HTTPException(status_code=404, detail="Call not found")

        call_data = call.data
        now = datetime.now(timezone.utc)
        started = datetime.fromisoformat(call_data["started_at"].replace("Z", "+00:00"))
        duration = int((now - started).total_seconds())

        # Update active call
        supabase_admin.table("active_calls").update({
            "status": "ended", "ended_at": now.isoformat(), "duration_seconds": duration,
            "end_reason": "user_hangup"
        }).eq("id", call_id).execute()

        # Save to call history
        supabase_admin.table("call_history").insert({
            "caller_id": call_data["caller_id"], "receiver_id": call_data["receiver_id"],
            "call_type": call_data["call_type"], "duration_seconds": duration,
            "started_at": call_data["started_at"], "ended_at": now.isoformat()
        }).execute()

        # Update user stats
        for uid in [call_data["caller_id"], call_data["receiver_id"]]:
            if uid:
                self._update_user_stats(uid, duration)

        return {"call_id": call_id, "duration": duration, "status": "ended"}

    def _update_user_stats(self, user_id: str, duration_seconds: int):
        try:
            profile = supabase_admin.table("profiles").select(
                "total_calls, total_speaking_minutes, xp_points"
            ).eq("id", user_id).single().execute()
            if profile.data:
                supabase_admin.table("profiles").update({
                    "total_calls": profile.data["total_calls"] + 1,
                    "total_speaking_minutes": profile.data["total_speaking_minutes"] + (duration_seconds // 60),
                    "xp_points": profile.data["xp_points"] + max(10, duration_seconds // 6)
                }).eq("id", user_id).execute()

                # Update daily streak
                supabase_admin.table("streaks").upsert({
                    "user_id": user_id,
                    "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "speaking_minutes": duration_seconds // 60,
                    "calls_made": 1,
                    "xp_earned": max(10, duration_seconds // 6)
                }, on_conflict="user_id,date").execute()
        except Exception as e:
            logger.error(f"Stats update error: {str(e)}")

    async def get_call_history(self, user_id: str, limit: int = 20) -> list:
        result = supabase_admin.table("call_history").select("*").or_(
            f"caller_id.eq.{user_id},receiver_id.eq.{user_id}"
        ).order("started_at", desc=True).limit(limit).execute()
        return result.data or []

    async def rate_call(self, call_id: str, user_id: str, rating: int) -> dict:
        call = supabase_admin.table("call_history").select("*").eq("id", call_id).single().execute()
        if not call.data:
            raise HTTPException(status_code=404, detail="Call not found")

        field = "caller_rating" if call.data["caller_id"] == user_id else "receiver_rating"
        supabase_admin.table("call_history").update({field: rating}).eq("id", call_id).execute()
        return {"message": "Rating submitted"}

    async def get_active_calls_count(self) -> int:
        result = supabase_admin.table("active_calls").select("id", count="exact").eq("status", "active").execute()
        return result.count or 0


call_service = CallService()
