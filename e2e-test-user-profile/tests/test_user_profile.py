"""
User Profile Unit Tests - E2E Test Implementation
"""

import pytest
from src.user_profile import UserProfileService, UserProfile


class TestUpdateUsername:
    """测试 update_username 函数"""

    def test_update_username_success(self):
        """成功更新用户名"""
        service = UserProfileService()
        profile = service.update_username("user1", "JohnDoe")

        assert profile.user_id == "user1"
        assert profile.username == "JohnDoe"
        assert profile.updated_at is not None

    def test_update_username_empty_raises_error(self):
        """空用户名应抛出异常"""
        service = UserProfileService()

        with pytest.raises(ValueError, match="Username cannot be empty"):
            service.update_username("user1", "")

    def test_update_username_whitespace_raises_error(self):
        """纯空白用户名应抛出异常"""
        service = UserProfileService()

        with pytest.raises(ValueError, match="Username cannot be empty"):
            service.update_username("user1", "   ")

    def test_update_username_too_long_raises_error(self):
        """超长用户名应抛出异常"""
        service = UserProfileService()
        long_name = "a" * 51

        with pytest.raises(ValueError, match="Username too long"):
            service.update_username("user1", long_name)

    def test_update_username_trims_whitespace(self):
        """用户名应去除首尾空白"""
        service = UserProfileService()
        profile = service.update_username("user1", "  JohnDoe  ")

        assert profile.username == "JohnDoe"


class TestUpdateEmail:
    """测试 update_email 函数"""

    def test_update_email_success(self):
        """成功更新邮箱"""
        service = UserProfileService()
        profile = service.update_email("user1", "john@example.com")

        assert profile.email == "john@example.com"
        assert profile.updated_at is not None

    def test_update_email_invalid_format_raises_error(self):
        """无效邮箱格式应抛出异常"""
        service = UserProfileService()

        with pytest.raises(ValueError, match="Invalid email format"):
            service.update_email("user1", "invalid-email")

    def test_update_email_no_at_sign_raises_error(self):
        """无@符号的邮箱应抛出异常"""
        service = UserProfileService()

        with pytest.raises(ValueError, match="Invalid email format"):
            service.update_email("user1", "john.example.com")

    def test_update_email_converts_to_lowercase(self):
        """邮箱应转换为小写"""
        service = UserProfileService()
        profile = service.update_email("user1", "John@EXAMPLE.COM")

        assert profile.email == "john@example.com"


class TestUpdateAvatar:
    """测试 update_avatar 函数"""

    def test_update_avatar_success(self):
        """成功更新头像"""
        service = UserProfileService()
        profile = service.update_avatar("user1", "https://example.com/avatar.jpg")

        assert profile.avatar_url == "https://example.com/avatar.jpg"
        assert profile.updated_at is not None

    def test_update_avatar_http_success(self):
        """HTTP URL 头像更新成功"""
        service = UserProfileService()
        profile = service.update_avatar("user1", "http://example.com/avatar.jpg")

        assert profile.avatar_url == "http://example.com/avatar.jpg"

    def test_update_avatar_empty_raises_error(self):
        """空头像URL应抛出异常"""
        service = UserProfileService()

        with pytest.raises(ValueError, match="Avatar URL cannot be empty"):
            service.update_avatar("user1", "")

    def test_update_avatar_invalid_protocol_raises_error(self):
        """非HTTP(S)协议应抛出异常"""
        service = UserProfileService()

        with pytest.raises(ValueError, match="must start with http"):
            service.update_avatar("user1", "ftp://example.com/avatar.jpg")


class TestUserProfileService:
    """测试 UserProfileService 整体功能"""

    def test_multiple_updates_on_same_user(self):
        """同一用户多次更新"""
        service = UserProfileService()

        profile1 = service.update_username("user1", "John")
        profile2 = service.update_email("user1", "john@example.com")
        profile3 = service.update_avatar("user1", "https://example.com/avatar.jpg")

        assert profile1.user_id == profile2.user_id == profile3.user_id == "user1"
        assert profile3.username == "John"
        assert profile3.email == "john@example.com"
        assert profile3.avatar_url == "https://example.com/avatar.jpg"

    def test_get_profile(self):
        """获取用户资料"""
        service = UserProfileService()
        service.update_username("user1", "John")

        profile = service.get_profile("user1")
        assert profile is not None
        assert profile.username == "John"

    def test_get_profile_not_found(self):
        """获取不存在的用户资料"""
        service = UserProfileService()

        profile = service.get_profile("nonexistent")
        assert profile is None