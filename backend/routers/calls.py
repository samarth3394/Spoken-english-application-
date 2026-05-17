from fastapi import APIRouter, Depends
from middleware.auth_middleware import get_current_user
from services.call_service import call_service
from models.schemas import CallRating

router = APIRouter(prefix="/api/calls", tags=["Calls"])


@router.get("/history")
async def call_history(limit: int = 20, current_user: dict = Depends(get_current_user)):
    return await call_service.get_call_history(current_user["id"], limit)


@router.post("/{call_id}/end")
async def end_call(call_id: str, current_user: dict = Depends(get_current_user)):
    return await call_service.end_call(call_id, current_user["id"])


@router.post("/{call_id}/rate")
async def rate_call(call_id: str, rating: CallRating, current_user: dict = Depends(get_current_user)):
    return await call_service.rate_call(call_id, current_user["id"], rating.rating)


@router.get("/active-count")
async def active_count():
    count = await call_service.get_active_calls_count()
    return {"active_calls": count}
