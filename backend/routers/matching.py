# Matching & Calls routers (combined for conciseness)

from fastapi import APIRouter, Depends
from middleware.auth_middleware import get_current_user
from services.matching_service import matching_service
from services.call_service import call_service

router = APIRouter(prefix="/api/matching", tags=["Matching"])


@router.get("/online-count")
async def online_count():
    return await matching_service.get_online_count()
