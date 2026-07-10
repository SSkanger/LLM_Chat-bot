"""Asynchronous SQLite implementation of the storage contract."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

from models.schemas import Message, MessageRole, Preset, Session, User, UserConfig, utc_now
from storage.base import StorageBackend


SCHEMA_VERSION = 1

MIGRATIONS: tuple[tuple[int, str], ...] = (
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            default_model TEXT NOT NULL,
            default_preset_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (default_preset_id) REFERENCES presets(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS presets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            system_prompt TEXT NOT NULL,
            is_builtin INTEGER NOT NULL DEFAULT 0 CHECK (is_builtin IN (0, 1)),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE (user_id, name)
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_builtin_preset_name
            ON presets(name) WHERE user_id IS NULL;

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            model_name TEXT NOT NULL,
            preset_id INTEGER,
            total_prompt_tokens INTEGER NOT NULL DEFAULT 0 CHECK (total_prompt_tokens >= 0),
            total_completion_tokens INTEGER NOT NULL DEFAULT 0 CHECK (total_completion_tokens >= 0),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (preset_id) REFERENCES presets(id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_user_updated
            ON sessions(user_id, updated_at DESC);

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('human', 'ai', 'system')),
            content TEXT NOT NULL,
            prompt_tokens INTEGER NOT NULL DEFAULT 0 CHECK (prompt_tokens >= 0),
            completion_tokens INTEGER NOT NULL DEFAULT 0 CHECK (completion_tokens >= 0),
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_messages_session_created
            ON messages(session_id, created_at, id);

        CREATE TABLE IF NOT EXISTS user_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE (user_id, key)
        );
        """,
    ),
)


def _as_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _as_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


class SQLiteBackend(StorageBackend):
    """SQLite storage using one serialized aiosqlite connection."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path).resolve()
        self._connection: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        connection = await self._get_connection()
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """
        )
        cursor = await connection.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations")
        current_version = int((await cursor.fetchone())[0])
        for version, sql in MIGRATIONS:
            if version <= current_version:
                continue
            await connection.executescript(sql)
            await connection.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (version, _as_timestamp(utc_now())),
            )
        await connection.commit()

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def create_user(self, user: User) -> User:
        connection = await self._get_connection()
        cursor = await connection.execute(
            """
            INSERT INTO users(username, default_model, default_preset_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user.username,
                user.default_model,
                user.default_preset_id,
                _as_timestamp(user.created_at),
                _as_timestamp(user.updated_at),
            ),
        )
        await connection.commit()
        return user.model_copy(update={"id": cursor.lastrowid})

    async def get_user(self, user_id: int) -> User | None:
        row = await self._fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
        return self._user_from_row(row) if row else None

    async def get_user_by_username(self, username: str) -> User | None:
        row = await self._fetchone("SELECT * FROM users WHERE username = ?", (username.strip(),))
        return self._user_from_row(row) if row else None

    async def list_users(self) -> list[User]:
        rows = await self._fetchall("SELECT * FROM users ORDER BY created_at, id")
        return [self._user_from_row(row) for row in rows]

    async def update_user(self, user: User) -> User:
        self._require_id(user.id, "user")
        updated = user.model_copy(update={"updated_at": utc_now()})
        connection = await self._get_connection()
        cursor = await connection.execute(
            """
            UPDATE users
            SET username = ?, default_model = ?, default_preset_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                updated.username,
                updated.default_model,
                updated.default_preset_id,
                _as_timestamp(updated.updated_at),
                updated.id,
            ),
        )
        await connection.commit()
        self._require_changed(cursor.rowcount, "用户不存在")
        return updated

    async def delete_user(self, user_id: int) -> bool:
        return await self._delete("DELETE FROM users WHERE id = ?", (user_id,))

    async def create_session(self, session: Session) -> Session:
        connection = await self._get_connection()
        cursor = await connection.execute(
            """
            INSERT INTO sessions(
                user_id, title, model_name, preset_id, total_prompt_tokens,
                total_completion_tokens, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session.user_id,
                session.title,
                session.model_name,
                session.preset_id,
                session.total_prompt_tokens,
                session.total_completion_tokens,
                _as_timestamp(session.created_at),
                _as_timestamp(session.updated_at),
            ),
        )
        await connection.commit()
        return session.model_copy(update={"id": cursor.lastrowid})

    async def get_session(self, session_id: int) -> Session | None:
        row = await self._fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))
        return self._session_from_row(row) if row else None

    async def list_sessions(self, user_id: int) -> list[Session]:
        rows = await self._fetchall(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC, id DESC",
            (user_id,),
        )
        return [self._session_from_row(row) for row in rows]

    async def update_session(self, session: Session) -> Session:
        self._require_id(session.id, "session")
        updated = session.model_copy(update={"updated_at": utc_now()})
        connection = await self._get_connection()
        cursor = await connection.execute(
            """
            UPDATE sessions
            SET title = ?, model_name = ?, preset_id = ?, total_prompt_tokens = ?,
                total_completion_tokens = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                updated.title,
                updated.model_name,
                updated.preset_id,
                updated.total_prompt_tokens,
                updated.total_completion_tokens,
                _as_timestamp(updated.updated_at),
                updated.id,
            ),
        )
        await connection.commit()
        self._require_changed(cursor.rowcount, "会话不存在")
        return updated

    async def delete_session(self, session_id: int) -> bool:
        return await self._delete("DELETE FROM sessions WHERE id = ?", (session_id,))

    async def add_message(self, message: Message) -> Message:
        connection = await self._get_connection()
        cursor = await connection.execute(
            """
            INSERT INTO messages(
                session_id, role, content, prompt_tokens, completion_tokens, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message.session_id,
                message.role.value,
                message.content,
                message.prompt_tokens,
                message.completion_tokens,
                _as_timestamp(message.created_at),
            ),
        )
        await connection.commit()
        return message.model_copy(update={"id": cursor.lastrowid})

    async def list_messages(self, session_id: int) -> list[Message]:
        rows = await self._fetchall(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at, id",
            (session_id,),
        )
        return [self._message_from_row(row) for row in rows]

    async def update_message(self, message: Message) -> Message:
        self._require_id(message.id, "message")
        connection = await self._get_connection()
        cursor = await connection.execute(
            """
            UPDATE messages
            SET role = ?, content = ?, prompt_tokens = ?, completion_tokens = ?
            WHERE id = ?
            """,
            (
                message.role.value,
                message.content,
                message.prompt_tokens,
                message.completion_tokens,
                message.id,
            ),
        )
        await connection.commit()
        self._require_changed(cursor.rowcount, "消息不存在")
        return message

    async def delete_message(self, message_id: int) -> bool:
        return await self._delete("DELETE FROM messages WHERE id = ?", (message_id,))

    async def create_preset(self, preset: Preset) -> Preset:
        connection = await self._get_connection()
        cursor = await connection.execute(
            """
            INSERT INTO presets(
                user_id, name, description, system_prompt, is_builtin, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                preset.user_id,
                preset.name,
                preset.description,
                preset.system_prompt,
                int(preset.is_builtin),
                _as_timestamp(preset.created_at),
                _as_timestamp(preset.updated_at),
            ),
        )
        await connection.commit()
        return preset.model_copy(update={"id": cursor.lastrowid})

    async def list_presets(self, user_id: int | None = None) -> list[Preset]:
        if user_id is None:
            rows = await self._fetchall(
                "SELECT * FROM presets WHERE user_id IS NULL ORDER BY name, id"
            )
        else:
            rows = await self._fetchall(
                """
                SELECT * FROM presets
                WHERE user_id IS NULL OR user_id = ?
                ORDER BY is_builtin DESC, name, id
                """,
                (user_id,),
            )
        return [self._preset_from_row(row) for row in rows]

    async def update_preset(self, preset: Preset) -> Preset:
        self._require_id(preset.id, "preset")
        updated = preset.model_copy(update={"updated_at": utc_now()})
        connection = await self._get_connection()
        cursor = await connection.execute(
            """
            UPDATE presets
            SET name = ?, description = ?, system_prompt = ?, is_builtin = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                updated.name,
                updated.description,
                updated.system_prompt,
                int(updated.is_builtin),
                _as_timestamp(updated.updated_at),
                updated.id,
            ),
        )
        await connection.commit()
        self._require_changed(cursor.rowcount, "预设不存在")
        return updated

    async def delete_preset(self, preset_id: int) -> bool:
        return await self._delete("DELETE FROM presets WHERE id = ?", (preset_id,))

    async def get_user_config(self, user_id: int, key: str) -> UserConfig | None:
        row = await self._fetchone(
            "SELECT * FROM user_configs WHERE user_id = ? AND key = ?",
            (user_id, key),
        )
        return self._user_config_from_row(row) if row else None

    async def set_user_config(self, config: UserConfig) -> UserConfig:
        updated_at = utc_now()
        connection = await self._get_connection()
        await connection.execute(
            """
            INSERT INTO user_configs(user_id, key, value, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (config.user_id, config.key, config.value, _as_timestamp(updated_at)),
        )
        await connection.commit()
        saved = await self.get_user_config(config.user_id, config.key)
        if saved is None:
            raise RuntimeError("用户配置保存失败")
        return saved

    async def list_user_configs(self, user_id: int) -> list[UserConfig]:
        rows = await self._fetchall(
            "SELECT * FROM user_configs WHERE user_id = ? ORDER BY key",
            (user_id,),
        )
        return [self._user_config_from_row(row) for row in rows]

    async def delete_user_config(self, user_id: int, key: str) -> bool:
        return await self._delete(
            "DELETE FROM user_configs WHERE user_id = ? AND key = ?",
            (user_id, key),
        )

    async def list_tables(self) -> list[str]:
        rows = await self._fetchall(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return [str(row["name"]) for row in rows]

    async def schema_version(self) -> int:
        row = await self._fetchone("SELECT COALESCE(MAX(version), 0) AS version FROM schema_migrations")
        return int(row["version"]) if row else 0

    async def _get_connection(self) -> aiosqlite.Connection:
        if self._connection is None:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = await aiosqlite.connect(self.database_path)
            self._connection.row_factory = aiosqlite.Row
            await self._connection.execute("PRAGMA foreign_keys = ON")
            await self._connection.execute("PRAGMA journal_mode = WAL")
        return self._connection

    async def _fetchone(
        self, query: str, parameters: tuple[Any, ...] = ()
    ) -> aiosqlite.Row | None:
        connection = await self._get_connection()
        cursor = await connection.execute(query, parameters)
        return await cursor.fetchone()

    async def _fetchall(
        self, query: str, parameters: tuple[Any, ...] = ()
    ) -> list[aiosqlite.Row]:
        connection = await self._get_connection()
        cursor = await connection.execute(query, parameters)
        return list(await cursor.fetchall())

    async def _delete(self, query: str, parameters: tuple[Any, ...]) -> bool:
        connection = await self._get_connection()
        cursor = await connection.execute(query, parameters)
        await connection.commit()
        return cursor.rowcount > 0

    @staticmethod
    def _require_id(value: int | None, entity: str) -> None:
        if value is None:
            raise ValueError(f"更新 {entity} 前必须提供 id")

    @staticmethod
    def _require_changed(rowcount: int, message: str) -> None:
        if rowcount == 0:
            raise LookupError(message)

    @staticmethod
    def _user_from_row(row: aiosqlite.Row) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            default_model=row["default_model"],
            default_preset_id=row["default_preset_id"],
            created_at=_as_datetime(row["created_at"]),
            updated_at=_as_datetime(row["updated_at"]),
        )

    @staticmethod
    def _session_from_row(row: aiosqlite.Row) -> Session:
        return Session(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            model_name=row["model_name"],
            preset_id=row["preset_id"],
            total_prompt_tokens=row["total_prompt_tokens"],
            total_completion_tokens=row["total_completion_tokens"],
            created_at=_as_datetime(row["created_at"]),
            updated_at=_as_datetime(row["updated_at"]),
        )

    @staticmethod
    def _message_from_row(row: aiosqlite.Row) -> Message:
        return Message(
            id=row["id"],
            session_id=row["session_id"],
            role=MessageRole(row["role"]),
            content=row["content"],
            prompt_tokens=row["prompt_tokens"],
            completion_tokens=row["completion_tokens"],
            created_at=_as_datetime(row["created_at"]),
        )

    @staticmethod
    def _preset_from_row(row: aiosqlite.Row) -> Preset:
        return Preset(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            description=row["description"],
            system_prompt=row["system_prompt"],
            is_builtin=bool(row["is_builtin"]),
            created_at=_as_datetime(row["created_at"]),
            updated_at=_as_datetime(row["updated_at"]),
        )

    @staticmethod
    def _user_config_from_row(row: aiosqlite.Row) -> UserConfig:
        return UserConfig(
            id=row["id"],
            user_id=row["user_id"],
            key=row["key"],
            value=row["value"],
            updated_at=_as_datetime(row["updated_at"]),
        )
