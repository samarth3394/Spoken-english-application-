"""
Aspire English Hub - Analytics Service
========================================
Dashboard analytics and reporting.
"""

from config import settings
from supabase import create_client
from fastapi import HTTPException
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)
supabase_admin = create_client(settings.supabase_url, settings.supabase_service_key) if settings.supabase_service_key else None


class AnalyticsService:
    async def get_admin_dashboard_stats(self) -> dict:
        try:
            total = supabase_admin.table("profiles").select("id", count="exact").eq("role", "student").execute()
            online = supabase_admin.table("profiles").select("id", count="exact").eq("is_online", True).execute()
            active = supabase_admin.table("active_calls").select("id", count="exact").eq("status", "active").execute()
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            calls_today = supabase_admin.table("call_history").select("id", count="exact").gte("started_at", today).execute()
            ai_today = supabase_admin.table("ai_sessions").select("id", count="exact").gte("started_at", today).execute()

            return {
                "total_students": total.count or 0,
                "online_students": online.count or 0,
                "active_calls": active.count or 0,
                "calls_today": calls_today.count or 0,
                "ai_sessions_today": ai_today.count or 0
            }
        except Exception as e:
            logger.error(f"Admin stats error: {str(e)}")
            return {}

    async def get_student_dashboard(self, user_id: str) -> dict:
        try:
            profile = supabase_admin.table("profiles").select("*").eq("id", user_id).single().execute()
            if not profile.data:
                raise HTTPException(status_code=404, detail="Profile not found")

            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            streak = supabase_admin.table("streaks").select("*").eq("user_id", user_id).eq("date", today).execute()

            # Weekly progress (last 7 days)
            week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
            weekly = supabase_admin.table("streaks").select("*").eq("user_id", user_id).gte("date", week_ago).order("date").execute()

            # Recent scores
            scores = supabase_admin.table("speaking_scores").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()

            # Active challenges
            challenges = supabase_admin.table("user_challenges").select(
                "*, challenges(*)"
            ).eq("user_id", user_id).eq("is_completed", False).execute()

            # Recent achievements
            achievements = supabase_admin.table("user_achievements").select(
                "*, achievements(*)"
            ).eq("user_id", user_id).order("earned_at", desc=True).limit(5).execute()

            # Leaderboard position
            lb = supabase_admin.table("profiles").select("id", count="exact").eq(
                "role", "student").gt("xp_points", profile.data.get("xp_points", 0)).execute()

            return {
                "profile": profile.data,
                "today_minutes": streak.data[0]["speaking_minutes"] if streak.data else 0,
                "today_calls": streak.data[0]["calls_made"] if streak.data else 0,
                "weekly_progress": weekly.data or [],
                "recent_scores": scores.data or [],
                "active_challenges": challenges.data or [],
                "recent_achievements": achievements.data or [],
                "leaderboard_position": (lb.count or 0) + 1
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Student dashboard error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to load dashboard")

    async def get_leaderboard(self, limit: int = 50) -> list:
        result = supabase_admin.rpc("get_leaderboard", {"p_limit": limit}).execute()
        return result.data or []

    async def get_weekly_report(self, user_id: str) -> dict:
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
        streaks = supabase_admin.table("streaks").select("*").eq("user_id", user_id).gte("date", week_ago).execute()
        scores = supabase_admin.table("speaking_scores").select("*").eq("user_id", user_id).gte("created_at", week_ago).execute()

        total_min = sum(s.get("speaking_minutes", 0) for s in (streaks.data or []))
        total_calls = sum(s.get("calls_made", 0) for s in (streaks.data or []))
        total_ai = sum(s.get("ai_sessions_count", 0) for s in (streaks.data or []))

        score_data = scores.data or []
        avg = lambda field: round(sum(s.get(field, 0) for s in score_data) / max(len(score_data), 1), 1)

        return {
            "total_minutes": total_min, "total_calls": total_calls, "total_ai_sessions": total_ai,
            "avg_pronunciation": avg("pronunciation_score"), "avg_fluency": avg("fluency_score"),
            "avg_grammar": avg("grammar_score"), "avg_vocabulary": avg("vocabulary_score"),
            "days_active": len(streaks.data or [])
        }

    async def get_all_students(self, branch_id: str = None, batch_id: str = None) -> list:
        query = supabase_admin.table("profiles").select("*").eq("role", "student")
        if branch_id:
            query = query.eq("branch_id", branch_id)
        if batch_id:
            query = query.eq("batch_id", batch_id)
        result = query.order("created_at", desc=True).execute()
        return result.data or []


analytics_service = AnalyticsService()
