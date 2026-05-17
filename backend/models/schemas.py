"""
Aspire English Hub - Pydantic Models & Schemas
===============================================
Request/Response models for the API.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================
# Enums
# ============================================================

class UserRole(str, Enum):
    STUDENT = "student"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class ProficiencyLevel(str, Enum):
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    UPPER_INTERMEDIATE = "upper_intermediate"
    ADVANCED = "advanced"
    PROFICIENT = "proficient"

class AIMode(str, Enum):
    CASUAL = "casual"
    INTERVIEW = "interview"
    IELTS = "ielts"
    DEBATE = "debate"
    TOPIC_BASED = "topic_based"

class CallType(str, Enum):
    PEER = "peer"
    AI = "ai"

class ReportReason(str, Enum):
    TOXIC_LANGUAGE = "toxic_language"
    HARASSMENT = "harassment"
    SPAM = "spam"
    INAPPROPRIATE = "inappropriate"
    OTHER = "other"


# ============================================================
# Auth Schemas
# ============================================================

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=150)
    display_name: Optional[str] = Field(None, max_length=50)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    email: str
    role: str

class PasswordResetRequest(BaseModel):
    email: EmailStr


# ============================================================
# Profile Schemas
# ============================================================

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    proficiency_level: Optional[ProficiencyLevel] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None

class ProfileResponse(BaseModel):
    id: str
    full_name: str
    display_name: Optional[str]
    email: str
    role: str
    avatar_url: Optional[str]
    branch_id: Optional[str]
    batch_id: Optional[str]
    is_online: bool
    xp_points: int
    current_streak: int
    longest_streak: int
    total_calls: int
    total_ai_sessions: int
    total_speaking_minutes: int
    proficiency_level: str
    created_at: str


# ============================================================
# Branch & Batch Schemas
# ============================================================

class BranchCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=2, max_length=100)
    address: Optional[str] = None

class BranchUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

class BranchResponse(BaseModel):
    id: str
    name: str
    city: str
    address: Optional[str]
    is_active: bool
    created_at: str

class BatchCreate(BaseModel):
    branch_id: str
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    schedule: Optional[str] = None
    max_students: int = 50

class BatchUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schedule: Optional[str] = None
    max_students: Optional[int] = None
    is_active: Optional[bool] = None

class BatchResponse(BaseModel):
    id: str
    branch_id: str
    name: str
    description: Optional[str]
    schedule: Optional[str]
    max_students: int
    is_active: bool
    created_at: str


# ============================================================
# Matching & Call Schemas
# ============================================================

class JoinQueueRequest(BaseModel):
    pass  # User info comes from JWT

class QueueStatusResponse(BaseModel):
    status: str
    position: Optional[int] = None
    estimated_wait: Optional[int] = None
    matched_user_id: Optional[str] = None

class CallResponse(BaseModel):
    id: str
    caller_id: str
    receiver_id: str
    call_type: str
    status: str
    started_at: str
    duration_seconds: int

class CallRating(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


# ============================================================
# AI Practice Schemas
# ============================================================

class AISessionStart(BaseModel):
    mode: AIMode = AIMode.CASUAL
    topic: Optional[str] = None

class AIMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class AISessionResponse(BaseModel):
    id: str
    mode: str
    topic: Optional[str]
    messages: List[Dict[str, Any]]
    duration_seconds: int
    scores: Optional[Dict[str, float]] = None
    feedback: Optional[Dict[str, Any]] = None

class AIChatRequest(BaseModel):
    session_id: str
    message: str

class AIChatResponse(BaseModel):
    reply: str
    suggestions: Optional[List[str]] = None
    corrections: Optional[List[Dict[str, str]]] = None

class AIAudioRequest(BaseModel):
    session_id: str
    # Audio data sent as multipart form

class PronunciationResult(BaseModel):
    word: str
    score: float
    suggestion: Optional[str] = None


# ============================================================
# Dashboard & Analytics Schemas
# ============================================================

class DashboardStats(BaseModel):
    total_students: int
    online_students: int
    active_calls: int
    total_ai_sessions_today: int
    total_calls_today: int
    total_speaking_minutes_today: int

class StudentDashboard(BaseModel):
    profile: ProfileResponse
    xp_points: int
    current_streak: int
    today_minutes: int
    today_calls: int
    weekly_progress: List[Dict[str, Any]]
    recent_scores: List[Dict[str, Any]]
    active_challenges: List[Dict[str, Any]]
    recent_achievements: List[Dict[str, Any]]
    leaderboard_position: int

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    display_name: str
    avatar_url: Optional[str]
    xp_points: int
    current_streak: int
    proficiency_level: str

class WeeklyReport(BaseModel):
    total_minutes: int
    total_calls: int
    total_ai_sessions: int
    avg_pronunciation: float
    avg_fluency: float
    avg_grammar: float
    avg_vocabulary: float
    improvement_tips: List[str]
    words_learned: int
    filler_words_reduced: int


# ============================================================
# Report Schemas
# ============================================================

class ReportCreate(BaseModel):
    reported_user_id: Optional[str] = None
    call_id: Optional[str] = None
    reason: ReportReason
    description: Optional[str] = None

class ReportResponse(BaseModel):
    id: str
    reporter_id: str
    reported_user_id: Optional[str]
    reason: str
    status: str
    created_at: str


# ============================================================
# Admin Schemas
# ============================================================

class AssignBatch(BaseModel):
    user_id: str
    batch_id: str

class BanUser(BaseModel):
    user_id: str
    reason: str

class AdminUserResponse(BaseModel):
    id: str
    full_name: str
    display_name: Optional[str]
    email: str
    role: str
    branch_id: Optional[str]
    batch_id: Optional[str]
    is_online: bool
    is_banned: bool
    xp_points: int
    total_calls: int
    total_speaking_minutes: int
    created_at: str


# ============================================================
# WebSocket Message Schemas
# ============================================================

class WSMessage(BaseModel):
    type: str
    data: Dict[str, Any] = {}

class SignalingMessage(BaseModel):
    type: str  # offer, answer, ice-candidate
    target_user_id: str
    payload: Dict[str, Any]
