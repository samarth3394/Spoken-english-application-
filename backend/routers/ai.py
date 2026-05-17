"""
Aspire English Hub - AI Router
================================
AI practice endpoints: sessions, STT, TTS, analysis.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Response
from middleware.auth_middleware import get_current_user
from services.ai_service import ai_service
from models.schemas import AISessionStart, AIChatRequest
from config import settings
from supabase import create_client
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI Practice"])

supabase_admin = create_client(settings.supabase_url, settings.supabase_service_key) if settings.supabase_service_key else None


@router.post("/sessions/start")
async def start_session(req: AISessionStart, current_user: dict = Depends(get_current_user)):
    session = supabase_admin.table("ai_sessions").insert({
        "user_id": current_user["id"],
        "mode": req.mode,
        "topic": req.topic,
        "messages": []
    }).execute()
    if session.data:
        return {"session_id": session.data[0]["id"], "mode": req.mode, "topic": req.topic}
    return {"error": "Failed to create session"}


@router.post("/sessions/{session_id}/chat")
async def chat(session_id: str, req: AIChatRequest, current_user: dict = Depends(get_current_user)):
    session = supabase_admin.table("ai_sessions").select("*").eq("id", session_id).eq("user_id", current_user["id"]).single().execute()
    if not session.data:
        return {"error": "Session not found"}

    messages = session.data.get("messages", [])
    messages.append({"role": "user", "content": req.message})

    result = await ai_service.get_ai_response(messages, session.data["mode"], session.data.get("topic"))
    messages.append({"role": "assistant", "content": result["reply"]})

    supabase_admin.table("ai_sessions").update({"messages": messages}).eq("id", session_id).execute()
    return {"reply": result["reply"], "session_id": session_id}


@router.post("/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    return await ai_service.speech_to_text(audio)


@router.post("/text-to-speech")
async def text_to_speech(text: str, voice: str = "alloy", current_user: dict = Depends(get_current_user)):
    audio_bytes = await ai_service.text_to_speech(text, voice)
    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.post("/analyze")
async def analyze_speech(text: str, current_user: dict = Depends(get_current_user)):
    return await ai_service.analyze_speech(text)


@router.post("/sessions/{session_id}/end")
async def end_session(session_id: str, current_user: dict = Depends(get_current_user)):
    session = supabase_admin.table("ai_sessions").select("*").eq("id", session_id).eq("user_id", current_user["id"]).single().execute()
    if not session.data:
        return {"error": "Session not found"}

    now = datetime.now(timezone.utc)
    started = datetime.fromisoformat(session.data["started_at"].replace("Z", "+00:00"))
    duration = int((now - started).total_seconds())

    # Analyze full conversation
    full_text = " ".join(m["content"] for m in session.data.get("messages", []) if m["role"] == "user")
    analysis = await ai_service.analyze_speech(full_text) if full_text else {}

    supabase_admin.table("ai_sessions").update({
        "ended_at": now.isoformat(), "duration_seconds": duration,
        "ai_feedback": analysis,
        "pronunciation_score": analysis.get("pronunciation_score"),
        "grammar_score": analysis.get("grammar_score"),
        "fluency_score": analysis.get("fluency_score"),
        "vocabulary_score": analysis.get("vocabulary_score"),
        "confidence_score": analysis.get("confidence_score"),
        "overall_score": analysis.get("overall_score")
    }).eq("id", session_id).execute()

    # Save speaking score
    if analysis and not analysis.get("error"):
        supabase_admin.table("speaking_scores").insert({
            "user_id": current_user["id"], "session_id": session_id,
            **{k: analysis.get(k) for k in ["pronunciation_score", "grammar_score", "fluency_score",
                "vocabulary_score", "confidence_score", "overall_score"]}
        }).execute()

    # Update user stats
    profile = supabase_admin.table("profiles").select("total_ai_sessions, xp_points, total_speaking_minutes").eq("id", current_user["id"]).single().execute()
    if profile.data:
        supabase_admin.table("profiles").update({
            "total_ai_sessions": profile.data["total_ai_sessions"] + 1,
            "total_speaking_minutes": profile.data["total_speaking_minutes"] + (duration // 60),
            "xp_points": profile.data["xp_points"] + 15 + (duration // 12)
        }).eq("id", current_user["id"]).execute()

    return {"session_id": session_id, "duration": duration, "analysis": analysis}


@router.get("/topics")
async def get_topics():
    result = supabase_admin.table("conversation_topics").select("*").eq("is_active", True).execute()
    return result.data or []


@router.get("/topics/random")
async def random_topic(current_user: dict = Depends(get_current_user)):
    return await ai_service.generate_topic()
