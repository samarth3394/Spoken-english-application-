"""
Aspire English Hub - Admin Router
===================================
Admin endpoints: branch/batch management, user moderation, analytics.
"""

from fastapi import APIRouter, Depends, HTTPException
from middleware.auth_middleware import require_admin
from services.analytics_service import analytics_service
from models.schemas import (BranchCreate, BranchUpdate, BatchCreate, BatchUpdate, AssignBatch, BanUser)
from config import settings
from supabase import create_client

router = APIRouter(prefix="/api/admin", tags=["Admin"])
supabase_admin = create_client(settings.supabase_url, settings.supabase_service_key) if settings.supabase_service_key else None


# --- Dashboard ---
@router.get("/dashboard")
async def dashboard(admin: dict = Depends(require_admin)):
    return await analytics_service.get_admin_dashboard_stats()


# --- Branches ---
@router.get("/branches")
async def list_branches(admin: dict = Depends(require_admin)):
    result = supabase_admin.table("branches").select("*").order("created_at").execute()
    return result.data or []

@router.post("/branches")
async def create_branch(data: BranchCreate, admin: dict = Depends(require_admin)):
    result = supabase_admin.table("branches").insert(data.model_dump()).execute()
    return result.data[0] if result.data else {"error": "Failed"}

@router.put("/branches/{branch_id}")
async def update_branch(branch_id: str, data: BranchUpdate, admin: dict = Depends(require_admin)):
    updates = data.model_dump(exclude_none=True)
    result = supabase_admin.table("branches").update(updates).eq("id", branch_id).execute()
    return result.data[0] if result.data else {"error": "Not found"}

@router.delete("/branches/{branch_id}")
async def delete_branch(branch_id: str, admin: dict = Depends(require_admin)):
    supabase_admin.table("branches").delete().eq("id", branch_id).execute()
    return {"message": "Branch deleted"}


# --- Batches ---
@router.get("/batches")
async def list_batches(branch_id: str = None, admin: dict = Depends(require_admin)):
    query = supabase_admin.table("batches").select("*, branches(name)")
    if branch_id:
        query = query.eq("branch_id", branch_id)
    result = query.order("created_at").execute()
    return result.data or []

@router.post("/batches")
async def create_batch(data: BatchCreate, admin: dict = Depends(require_admin)):
    result = supabase_admin.table("batches").insert(data.model_dump()).execute()
    return result.data[0] if result.data else {"error": "Failed"}

@router.put("/batches/{batch_id}")
async def update_batch(batch_id: str, data: BatchUpdate, admin: dict = Depends(require_admin)):
    updates = data.model_dump(exclude_none=True)
    result = supabase_admin.table("batches").update(updates).eq("id", batch_id).execute()
    return result.data[0] if result.data else {"error": "Not found"}

@router.delete("/batches/{batch_id}")
async def delete_batch(batch_id: str, admin: dict = Depends(require_admin)):
    supabase_admin.table("batches").delete().eq("id", batch_id).execute()
    return {"message": "Batch deleted"}


# --- Students ---
@router.get("/students")
async def list_students(branch_id: str = None, batch_id: str = None, admin: dict = Depends(require_admin)):
    return await analytics_service.get_all_students(branch_id, batch_id)

@router.post("/students/assign-batch")
async def assign_batch(data: AssignBatch, admin: dict = Depends(require_admin)):
    batch = supabase_admin.table("batches").select("branch_id").eq("id", data.batch_id).single().execute()
    if not batch.data:
        raise HTTPException(status_code=404, detail="Batch not found")
    result = supabase_admin.table("profiles").update({
        "batch_id": data.batch_id, "branch_id": batch.data["branch_id"]
    }).eq("id", data.user_id).execute()
    return result.data[0] if result.data else {"error": "Failed"}

@router.post("/students/ban")
async def ban_user(data: BanUser, admin: dict = Depends(require_admin)):
    supabase_admin.table("profiles").update({
        "is_banned": True, "ban_reason": data.reason
    }).eq("id", data.user_id).execute()
    return {"message": "User banned"}

@router.post("/students/{user_id}/unban")
async def unban_user(user_id: str, admin: dict = Depends(require_admin)):
    supabase_admin.table("profiles").update({
        "is_banned": False, "ban_reason": None
    }).eq("id", user_id).execute()
    return {"message": "User unbanned"}


# --- Reports ---
@router.get("/reports")
async def list_reports(status: str = "pending", admin: dict = Depends(require_admin)):
    result = supabase_admin.table("reports").select("*").eq("status", status).order("created_at", desc=True).execute()
    return result.data or []

@router.put("/reports/{report_id}")
async def update_report(report_id: str, status: str, notes: str = None, admin: dict = Depends(require_admin)):
    from datetime import datetime, timezone
    supabase_admin.table("reports").update({
        "status": status, "admin_notes": notes,
        "reviewed_by": admin["id"],
        "reviewed_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", report_id).execute()
    return {"message": "Report updated"}


# --- Call Analytics ---
@router.get("/calls/active")
async def active_calls(admin: dict = Depends(require_admin)):
    result = supabase_admin.table("active_calls").select("*").eq("status", "active").execute()
    return result.data or []
