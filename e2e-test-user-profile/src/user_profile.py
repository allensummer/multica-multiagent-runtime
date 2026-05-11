"""
User Profile Module - E2E Test Implementation
更新用户资料功能实现
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class UserProfile:
    """用户资料数据类"""
    user_id: str
    username: str = ""
    email: str = ""
    avatar_url: str = ""
    updated_at: Optional[str] = None


class UserProfileService:
    """用户资料服务"""

    def __init__(self):
        self._profiles: dict[str, UserProfile] = {}

    def update_username(self, user_id: str, new_username: str) -> UserProfile:
        """
        更新用户昵称

        Args:
            user_id: 用户ID
            new_username: 新昵称

        Returns:
            更新后的用户资料

        Raises:
            ValueError: 如果新昵称为空或格式无效
        """
        if not new_username or len(new_username.strip()) == 0:
            raise ValueError("Username cannot be empty")

        if len(new_username) > 50:
            raise ValueError("Username too long (max 50 characters)")

        profile = self._profiles.get(user_id, UserProfile(user_id=user_id))
        profile.username = new_username.strip()
        profile.updated_at = datetime.now().isoformat()
        self._profiles[user_id] = profile

        return profile

    def update_email(self, user_id: str, new_email: str) -> UserProfile:
        """
        更新用户邮箱

        Args:
            user_id: 用户ID
            new_email: 新邮箱

        Returns:
            更新后的用户资料

        Raises:
            ValueError: 如果邮箱格式无效
        """
        if not new_email or "@" not in new_email:
            raise ValueError("Invalid email format")

        if len(new_email) > 100:
            raise ValueError("Email too long (max 100 characters)")

        profile = self._profiles.get(user_id, UserProfile(user_id=user_id))
        profile.email = new_email.strip().lower()
        profile.updated_at = datetime.now().isoformat()
        self._profiles[user_id] = profile

        return profile

    def update_avatar(self, user_id: str, new_avatar_url: str) -> UserProfile:
        """
        更新用户头像

        Args:
            user_id: 用户ID
            new_avatar_url: 新头像URL

        Returns:
            更新后的用户资料

        Raises:
            ValueError: 如果头像URL格式无效
        """
        if not new_avatar_url:
            raise ValueError("Avatar URL cannot be empty")

        if not (new_avatar_url.startswith("http://") or new_avatar_url.startswith("https://")):
            raise ValueError("Avatar URL must start with http:// or https://")

        profile = self._profiles.get(user_id, UserProfile(user_id=user_id))
        profile.avatar_url = new_avatar_url
        profile.updated_at = datetime.now().isoformat()
        self._profiles[user_id] = profile

        return profile

    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户资料"""
        return self._profiles.get(user_id)

    def get_all_profiles(self) -> dict[str, UserProfile]:
        """获取所有用户资料"""
        return self._profiles.copy()