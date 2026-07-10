"""User lifecycle and active-user isolation logic."""

from __future__ import annotations

from models.schemas import Preset, Session, User, UserConfig
from storage.base import StorageBackend


class UserManagerError(RuntimeError):
    """Base error for user-management operations."""


class DuplicateUsernameError(UserManagerError):
    """Raised when a username is already persisted."""


class UserNotFoundError(UserManagerError):
    """Raised when a requested user does not exist."""


class NoActiveUserError(UserManagerError):
    """Raised when an isolated operation has no selected user."""


class UserManager:
    """Manage persisted users and the active isolated user context."""

    def __init__(self, storage: StorageBackend, default_model: str = "mock") -> None:
        self.storage = storage
        self.default_model = default_model
        self.current_user: User | None = None

    async def create_user(self, username: str, default_model: str | None = None) -> User:
        normalized = username.strip()
        if not normalized:
            raise ValueError("用户名不能为空")
        if await self.storage.get_user_by_username(normalized) is not None:
            raise DuplicateUsernameError(f"用户名“{normalized}”已存在")
        user = await self.storage.create_user(
            User(username=normalized, default_model=default_model or self.default_model)
        )
        if self.current_user is None:
            self.current_user = user
        return user

    async def list_users(self) -> list[User]:
        return await self.storage.list_users()

    async def resolve_user(self, identifier: int | str) -> User:
        user: User | None
        if isinstance(identifier, int) or str(identifier).strip().isdigit():
            user = await self.storage.get_user(int(identifier))
        else:
            user = await self.storage.get_user_by_username(str(identifier).strip())
        if user is None:
            raise UserNotFoundError(f"找不到用户：{identifier}")
        return user

    async def switch_user(self, identifier: int | str) -> User:
        user = await self.resolve_user(identifier)
        self.current_user = user
        return user

    async def delete_user(self, identifier: int | str) -> User:
        user = await self.resolve_user(identifier)
        if user.id is None or not await self.storage.delete_user(user.id):
            raise UserNotFoundError(f"找不到用户：{identifier}")
        if self.current_user and self.current_user.id == user.id:
            self.current_user = None
        return user

    def require_current_user(self) -> User:
        if self.current_user is None:
            raise NoActiveUserError("请先创建或切换用户")
        return self.current_user

    async def list_current_user_sessions(self) -> list[Session]:
        user = self.require_current_user()
        if user.id is None:
            return []
        return await self.storage.list_sessions(user.id)

    async def list_current_user_presets(self) -> list[Preset]:
        user = self.require_current_user()
        if user.id is None:
            return []
        return await self.storage.list_presets(user.id)

    async def list_current_user_configs(self) -> list[UserConfig]:
        user = self.require_current_user()
        if user.id is None:
            return []
        return await self.storage.list_user_configs(user.id)
