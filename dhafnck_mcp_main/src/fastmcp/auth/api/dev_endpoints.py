"""
Development-only endpoints for testing authentication
WARNING: These endpoints should NEVER be exposed in production!
"""

import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..infrastructure.supabase_auth import SupabaseAuthService

logger = logging.getLogger(__name__)

# Only enable in development mode
if os.getenv("ENVIRONMENT", "development") != "development":
    router = APIRouter()
else:
    router = APIRouter(prefix="/auth/dev", tags=["Development Auth"])
    
    class DevConfirmRequest(BaseModel):
        email: str
    
    
    @router.post("/confirm-user")
    async def dev_confirm_user(request: DevConfirmRequest):
        """
        DEVELOPMENT ONLY: Manually confirm a user without email verification.
        This endpoint bypasses email verification for testing purposes.
        
        ⚠️ WARNING: Never expose this in production!
        """
        try:
            # Initialize Supabase service
            supabase_service = SupabaseAuthService()
            
            # Use admin client to manually confirm user
            # Note: This requires SUPABASE_SERVICE_ROLE_KEY
            response = supabase_service.admin_client.auth.admin.list_users()
            
            # Find the user by email
            user_found = None
            for user in response.users:
                if user.email == request.email:
                    user_found = user
                    break
            
            if not user_found:
                raise HTTPException(status_code=404, detail="User not found")
            
            if user_found.email_confirmed_at:
                return {
                    "success": True,
                    "message": "User already confirmed",
                    "confirmed_at": user_found.email_confirmed_at
                }
            
            # Update user to confirm email
            update_response = supabase_service.admin_client.auth.admin.update_user_by_id(
                user_found.id,
                {"email_confirmed_at": "now()"}
            )
            
            logger.info(f"[DEV] Manually confirmed user: {request.email}")
            
            return {
                "success": True,
                "message": f"User {request.email} manually confirmed (DEV MODE)",
                "warning": "This is a development-only feature"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"[DEV] Manual confirmation error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to manually confirm user: {str(e)}"
            )
    
    
    @router.get("/list-unconfirmed")
    async def dev_list_unconfirmed_users():
        """
        DEVELOPMENT ONLY: List all unconfirmed users.
        Useful for debugging email verification issues.
        """
        try:
            supabase_service = SupabaseAuthService()
            response = supabase_service.admin_client.auth.admin.list_users()
            
            unconfirmed = []
            for user in response.users:
                if not user.email_confirmed_at:
                    unconfirmed.append({
                        "id": user.id,
                        "email": user.email,
                        "created_at": user.created_at,
                        "last_sign_in": user.last_sign_in_at
                    })
            
            return {
                "total_unconfirmed": len(unconfirmed),
                "users": unconfirmed,
                "warning": "This is a development-only feature"
            }
            
        except Exception as e:
            logger.error(f"[DEV] List unconfirmed error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list unconfirmed users: {str(e)}"
            )
    
    
    @router.get("/email-status")
    async def dev_check_email_status():
        """
        DEVELOPMENT ONLY: Check email configuration status.
        Shows current email settings and limitations.
        """
        try:
            return {
                "environment": os.getenv("ENVIRONMENT", "development"),
                "smtp_configured": bool(os.getenv("SMTP_HOST")),
                "supabase_configured": bool(os.getenv("SUPABASE_URL")),
                "rate_limits": {
                    "free_tier": "3-4 emails per hour",
                    "current_status": "Check Supabase Dashboard → Auth → Logs"
                },
                "recommendations": [
                    "For development: Use /auth/dev/confirm-user endpoint",
                    "For production: Configure custom SMTP",
                    "Alternative: Use Supabase Dashboard to manually confirm users"
                ],
                "warning": "This is a development-only feature"
            }
            
        except Exception as e:
            logger.error(f"[DEV] Email status check error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to check email status: {str(e)}"
            )