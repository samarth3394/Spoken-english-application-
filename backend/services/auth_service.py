"""
Aspire English Hub - Authentication Service
=============================================
Handles user registration, login, and session management via Supabase Auth.
"""

from config import settings
from supabase import create_client
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase clients
supabase = create_client(settings.supabase_url, settings.supabase_key) if settings.supabase_key else None
supabase_admin = create_client(settings.supabase_url, settings.supabase_service_key) if settings.supabase_service_key else None


class AuthService:
    """Authentication service using Supabase Auth."""
    
    @staticmethod
    async def signup(email: str, password: str, full_name: str, display_name: str = None):
        """Register a new user."""
        try:
            result = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "display_name": display_name or full_name.split()[0]
                    }
                }
            })
            
            if result.user:
                return {
                    "user_id": result.user.id,
                    "email": result.user.email,
                    "access_token": result.session.access_token if result.session else None,
                    "refresh_token": result.session.refresh_token if result.session else None,
                    "message": "Account created successfully"
                }
            else:
                raise HTTPException(status_code=400, detail="Signup failed")
                
        except Exception as e:
            logger.error(f"Signup error: {str(e)}")
            error_msg = str(e)
            if "already registered" in error_msg.lower():
                raise HTTPException(status_code=409, detail="Email already registered")
            raise HTTPException(status_code=400, detail=f"Signup failed: {error_msg}")
    
    @staticmethod
    async def login(email: str, password: str):
        """Authenticate user and return session tokens."""
        try:
            result = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if result.user and result.session:
                # Get user profile
                profile = supabase_admin.table("profiles").select("*").eq("id", result.user.id).single().execute()
                
                # Check if user is banned
                if profile.data and profile.data.get("is_banned"):
                    raise HTTPException(status_code=403, detail="Account has been suspended")
                
                return {
                    "access_token": result.session.access_token,
                    "refresh_token": result.session.refresh_token,
                    "user_id": result.user.id,
                    "email": result.user.email,
                    "role": profile.data.get("role", "student") if profile.data else "student",
                    "expires_at": result.session.expires_at
                }
            else:
                raise HTTPException(status_code=401, detail="Invalid credentials")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
    
    @staticmethod
    async def logout(token: str):
        """Sign out user and invalidate session."""
        try:
            supabase.auth.sign_out()
            return {"message": "Logged out successfully"}
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return {"message": "Logged out"}
    
    @staticmethod
    async def refresh_token(refresh_token: str):
        """Refresh access token using refresh token."""
        try:
            result = supabase.auth.refresh_session(refresh_token)
            if result.session:
                return {
                    "access_token": result.session.access_token,
                    "refresh_token": result.session.refresh_token,
                    "expires_at": result.session.expires_at
                }
            raise HTTPException(status_code=401, detail="Token refresh failed")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    @staticmethod
    async def reset_password(email: str):
        """Send password reset email."""
        try:
            supabase.auth.reset_password_email(email, {
                "redirect_to": f"{settings.frontend_url}/reset-password"
            })
            return {"message": "Password reset email sent"}
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            # Don't reveal if email exists or not
            return {"message": "If the email exists, a reset link has been sent"}
    
    @staticmethod
    async def get_profile(user_id: str):
        """Get user profile from database."""
        try:
            result = supabase_admin.table("profiles").select("*").eq("id", user_id).single().execute()
            if result.data:
                return result.data
            raise HTTPException(status_code=404, detail="Profile not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get profile error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch profile")
    
    @staticmethod
    async def update_profile(user_id: str, updates: dict):
        """Update user profile."""
        try:
            # Filter out None values
            clean_updates = {k: v for k, v in updates.items() if v is not None}
            if not clean_updates:
                raise HTTPException(status_code=400, detail="No updates provided")
            
            result = supabase_admin.table("profiles").update(clean_updates).eq("id", user_id).execute()
            if result.data:
                return result.data[0]
            raise HTTPException(status_code=404, detail="Profile not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Update profile error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update profile")
    
    @staticmethod
    async def set_online_status(user_id: str, is_online: bool):
        """Update user online status."""
        try:
            update_data = {"is_online": is_online}
            if not is_online:
                update_data["last_seen"] = "now()"
            
            supabase_admin.table("profiles").update(update_data).eq("id", user_id).execute()
        except Exception as e:
            logger.error(f"Online status update error: {str(e)}")


auth_service = AuthService()
