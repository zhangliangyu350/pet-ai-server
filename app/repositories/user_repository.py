from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        """Create a user repository bound to a database session."""
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Return a user by primary key."""
        return self.db.get(User, user_id)

    def get_by_openid(self, openid: str) -> Optional[User]:
        """Return a user by WeChat openid."""
        statement = select(User).where(User.openid == openid)
        return self.db.execute(statement).scalar_one_or_none()

    def create(self, user: User) -> User:
        """Persist a new user in the current transaction."""
        self.db.add(user)
        self.db.flush()
        return user

    def upsert_wechat_user(
        self,
        user_id: str,
        openid: str,
        nickname: str = "微信用户",
        avatar_url: str = "",
    ) -> User:
        """Create or update a user based on WeChat identity."""
        user = self.get_by_openid(openid)
        if user is None:
            user = User(id=user_id, openid=openid, nickname=nickname, avatar_url=avatar_url)
            return self.create(user)

        user.nickname = nickname or user.nickname
        user.avatar_url = avatar_url or user.avatar_url
        self.db.flush()
        return user
