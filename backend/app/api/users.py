"""Users API."""
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Return current authenticated user profile."""
    return {
        "success": True,
        "data": {
            "id": str(current_user.id),
            "name": current_user.name,
            "phone": current_user.phone,
            "is_active": current_user.is_active,
            "is_phone_verified": current_user.is_phone_verified,
            "created_at": current_user.created_at.isoformat(),
            "updated_at": current_user.updated_at.isoformat(),
        },
    }
