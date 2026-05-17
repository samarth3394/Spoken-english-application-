"""
Aspire English Hub - Students Router
======================================
Student-facing endpoints: dashboard, queue, history, challenges, leaderboard.
"""

from fastapi import APIRouter, Depends
from middleware.auth_middleware import get_current_user
from services.matching_service import matching_service
from services.call_service import call_service
from services.analytics_service import analytics_service
from models.schemas import CallRating

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.get("/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    return await analytics_service.get_student_dashboard(current_user["id"])


@router.post("/queue/join")
async def join_queue(current_user: dict = Depends(get_current_user)):
    return await matching_service.join_queue(current_user["id"])


@router.post("/queue/leave")
async def leave_queue(current_user: dict = Depends(get_current_user)):
    return await matching_service.leave_queue(current_user["id"])


@router.get("/queue/status")
async def queue_status(current_user: dict = Depends(get_current_user)):
    return await matching_service.get_queue_status(current_user["id"])


@router.get("/calls/history")
async def call_history(limit: int = 20, current_user: dict = Depends(get_current_user)):
    return await call_service.get_call_history(current_user["id"], limit)


@router.post("/calls/{call_id}/end")
async def end_call(call_id: str, current_user: dict = Depends(get_current_user)):
    return await call_service.end_call(call_id, current_user["id"])


@router.post("/calls/{call_id}/rate")
async def rate_call(call_id: str, rating: CallRating, current_user: dict = Depends(get_current_user)):
    return await call_service.rate_call(call_id, current_user["id"], rating.rating)


@router.get("/leaderboard")
async def leaderboard(limit: int = 50):
    return await analytics_service.get_leaderboard(limit)


@router.get("/reports/weekly")
async def weekly_report(current_user: dict = Depends(get_current_user)):
    return await analytics_service.get_weekly_report(current_user["id"])


@router.get("/online-count")
async def online_count():
    return await matching_service.get_online_count()
