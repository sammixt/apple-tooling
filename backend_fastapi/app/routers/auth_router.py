from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth.google import get_google_auth_url, get_google_user_info
from app.auth.jwt import create_access_token
from app.db.database import get_db
from app.db.models import User, Role
from sqlalchemy.sql import func
from sqlalchemy import or_, and_
import traceback

router = APIRouter()


@router.get("/auth/google")
def google_login():
    """Get the Google OAuth login URL."""
    return {"auth_url": get_google_auth_url()}

@router.get("/auth/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback."""
    try:
        google_user = get_google_user_info(code)
        if not google_user["email"].endswith('@turing.com'):
            raise HTTPException(status_code=401, detail="User outside the organization is not allowed to login.")
        
        # user = db.query(User).filter(User.google_auth_id == google_user["id"]).first()
        user = db.query(User).filter(
            and_(
                User.is_active == True,  # Ensure the user is active
                or_(
                    User.google_auth_id == google_user["id"],
                    User.email == google_user["email"]
                )
            )
        ).first()
        
        if not user:
            # Fetch or create minimal permissions role only if the user doesn't exist
            role = db.query(Role).filter(
                and_(
                    Role.name == "Viewer",
                    Role.deleted_at.is_(None)
                )
            ).first()

            if not role:
                minimal_permissions = {
                    "logs": False,
                    "upload_to_s3": False,
                    "configuration": False,
                    "user_management": False,
                    "download_from_s3": False,
                }
                role = Role(
                    name="Viewer",
                    description="Role with minimal permissions",
                    permissions=minimal_permissions,
                    created_at=func.now(),
                )
                db.add(role)
                db.commit()
                db.refresh(role)

            # Prepare role data
            role_data = {
                "id": role.id,
                "name": role.name,
                "permissions": role.permissions
            } if role else None

            # Create a new user
            user = User(
                google_auth_id=google_user["id"],
                email=google_user["email"],
                name=google_user["name"],
                profile_pic_url=google_user["picture"],
                role_id=role.id,
                is_active=True,
                created_at=func.now(),
                updated_at=func.now(),
                last_login_at=func.now()
            )
            db.add(user)
        else:
            user.google_auth_id=google_user["id"]
            user.email=google_user["email"]
            user.name=google_user["name"]
            user.profile_pic_url=google_user["picture"]
            user.last_login_at = func.now()

            # Fetch the user's role
            role = None
            if user.role_id:
                role = db.query(Role).filter(
                    and_(
                        Role.id == user.role_id,
                        Role.deleted_at.is_(None)  # Exclude soft-deleted roles
                    )
                ).first()

            # Prepare role data
            role_data = {
                "id": role.id,
                "name": role.name,
                "permissions": role.permissions
            } if role else None

        db.commit()
        db.refresh(user)

        # Create JWT token
        token = create_access_token({"id": user.id, "sub": user.google_auth_id, "name": user.name, "profile_pic_url": user.profile_pic_url, "email": user.email})
        return {"access_token": token, "token_type": "bearer", "id": user.id, "sub": user.google_auth_id, "name": user.name, "profile_pic_url": user.profile_pic_url, "email": user.email, "role": role_data}
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))
