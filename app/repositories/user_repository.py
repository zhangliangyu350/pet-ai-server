from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        """创建绑定到数据库会话的用户仓储。"""
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        """按主键返回用户。"""
        return self.db.get(User, user_id)

    def get_by_openid(self, openid: str) -> Optional[User]:
        """按微信 openid 返回用户。"""
        statement = select(User).where(User.openid == openid)
        return self.db.execute(statement).scalar_one_or_none()

    def create(self, user: User) -> User:
        """在当前事务中持久化新用户。"""
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
        """根据微信身份创建或更新用户。"""
        user = self.get_by_openid(openid)
        if user is None:
            user = User(id=user_id, openid=openid, nickname=nickname, avatar_url=avatar_url)
            return self.create(user)

        user.nickname = nickname or user.nickname
        user.avatar_url = avatar_url or user.avatar_url
        self.db.flush()
        return user
