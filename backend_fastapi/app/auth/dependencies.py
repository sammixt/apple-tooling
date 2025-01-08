from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.auth.jwt import decode_access_token
from app.db.database import get_db
from app.db.models import User, Role
from typing import Callable

# HTTPBearer extracts the Bearer token from the Authorization header
security = HTTPBearer()
user_session = {}

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
):
    """Validate the JWT token and return the current user."""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Set session info for activity logs
        user_session["user_id"] = user.id
        
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def has_permission(permission: str) -> Callable:
    def permission_dependency(
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db),
    ):
        # Ensure the user has a role assigned
        if not current_user.role_id:
            raise HTTPException(status_code=403, detail="User has no role assigned")

        print(current_user.role_id)
        # Fetch the user's role, ensuring it's not soft-deleted
        role = db.query(Role).filter(
            Role.id == current_user.role_id,
            Role.deleted_at.is_(None)  # Role must not be soft-deleted
        ).first()

        if not role:
            raise HTTPException(status_code=403, detail="Assigned role does not exist or is deleted")

        # Fetch the permissions from the role
        permissions = role.permissions or {}
        if not permissions.get(permission, False):
            raise HTTPException(status_code=403, detail=f"Permission '{permission}' is required")

    return permission_dependency
