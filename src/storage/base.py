"""Abstract asynchronous contract implemented by every storage backend."""

from __future__ import annotations

from abc import ABC, abstractmethod

from models.schemas import Message, Preset, Session, User, UserConfig


class StorageBackend(ABC):
    """Persistence boundary shared by SQLite, MySQL and file backends."""

    @abstractmethod
    async def initialize(self) -> None:
        """Prepare the backend and create required structures."""

    @abstractmethod
    async def close(self) -> None:
        """Release backend resources."""

    @abstractmethod
    async def create_user(self, user: User) -> User:
        """Persist and return a user."""

    @abstractmethod
    async def get_user(self, user_id: int) -> User | None:
        """Return a user by primary key."""

    @abstractmethod
    async def list_users(self) -> list[User]:
        """Return all users."""

    @abstractmethod
    async def delete_user(self, user_id: int) -> bool:
        """Delete a user and return whether a record changed."""

    @abstractmethod
    async def create_session(self, session: Session) -> Session:
        """Persist and return a conversation session."""

    @abstractmethod
    async def get_session(self, session_id: int) -> Session | None:
        """Return a session by primary key."""

    @abstractmethod
    async def list_sessions(self, user_id: int) -> list[Session]:
        """Return sessions owned by a user."""

    @abstractmethod
    async def update_session(self, session: Session) -> Session:
        """Persist session changes."""

    @abstractmethod
    async def delete_session(self, session_id: int) -> bool:
        """Delete a session and its messages."""

    @abstractmethod
    async def add_message(self, message: Message) -> Message:
        """Append a message to a session."""

    @abstractmethod
    async def list_messages(self, session_id: int) -> list[Message]:
        """Return messages in chronological order."""

    @abstractmethod
    async def create_preset(self, preset: Preset) -> Preset:
        """Persist and return a preset."""

    @abstractmethod
    async def list_presets(self, user_id: int | None = None) -> list[Preset]:
        """Return built-in presets plus optional user presets."""

    @abstractmethod
    async def update_preset(self, preset: Preset) -> Preset:
        """Persist preset changes."""

    @abstractmethod
    async def delete_preset(self, preset_id: int) -> bool:
        """Delete a user preset."""

    @abstractmethod
    async def get_user_config(self, user_id: int, key: str) -> UserConfig | None:
        """Read one user preference."""

    @abstractmethod
    async def set_user_config(self, config: UserConfig) -> UserConfig:
        """Create or update a user preference."""
