from datetime import datetime

from core.database import SessionLocal
from core.models import User


class UserService:
    def get(self, user_id: int) -> User | None:
        db = SessionLocal()

        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()

    def upsert_oauth_user(
        self,
        *,
        provider: str,
        subject: str,
        name: str,
        username: str | None,
        email: str | None,
        profile_picture_url: str | None,
    ) -> User:
        oauth_login_id = f"{provider}:{subject}"
        db = SessionLocal()

        try:
            user = db.query(User).filter(User.oauth_login_id == oauth_login_id).first()
            now = datetime.utcnow()

            if user is None:
                user = User(
                    name=name,
                    username=username or name,
                    email=email,
                    oauth_login_id=oauth_login_id,
                    oauth_provider=provider,
                    oauth_subject=subject,
                    profile_picture_url=profile_picture_url,
                    role="user",
                    created_at=now,
                    updated_at=now,
                )
                db.add(user)
            else:
                user.name = name
                user.username = username or name
                user.email = email
                user.oauth_provider = provider
                user.oauth_subject = subject
                user.profile_picture_url = profile_picture_url
                user.updated_at = now

            db.commit()
            db.refresh(user)
            db.expunge(user)
            return user
        finally:
            db.close()


user_service = UserService()
