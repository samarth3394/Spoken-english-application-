"""
Aspire English Hub - Authentication Middleware
===============================================
JWT validation and user extraction middleware.
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from config import settings
from supabase import create_client
import httpx

security = HTTPBearer()

# Initialize Supabase client
supabase = create_client(settings.supabase_url, settings.supabase_service_key) if settings.supabase_service_key else None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and return user data."""
    token = credentials.credentials
    
    try:
        # Decode the Supabase JWT
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated"
        )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token: no user ID")
        
        # Get user profile from Supabase
        if supabase:
            result = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
            if result.data:
                user_data = result.data
                user_data["token"] = token
                return user_data
        
        # Fallback: return basic payload data
        return {
            "id": user_id,
            "email": payload.get("email", ""),
            "role": payload.get("role", "student"),
            "token": token
        }
        
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


async def require_admin(current_user: dict = Depends(get_current_user)):
    """Require admin role for access."""
    if current_user.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def require_super_admin(current_user: dict = Depends(get_current_user)):
    """Require super admin role for access."""
    if current_user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user
