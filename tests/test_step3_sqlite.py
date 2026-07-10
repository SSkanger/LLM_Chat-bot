from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio

from config_manager import ProjectConfig, StorageSection
from models.schemas import Message, MessageRole, Preset, Session, User, UserConfig
from storage.factory import StorageFactory
from storage.sqlite_backend import SCHEMA_VERSION, SQLiteBackend


@pytest_asyncio.fixture
async def backend():
    database_path = Path("data/test") / f"step3-{uuid4().hex}.db"
    storage = SQLiteBackend(database_path)
    await storage.initialize()
    try:
        yield storage
    finally:
        await storage.close()
        for candidate in (
            storage.database_path,
            Path(f"{storage.database_path}-wal"),
            Path(f"{storage.database_path}-shm"),
        ):
            candidate.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_initialization_creates_all_tables(backend: SQLiteBackend) -> None:
    assert set(await backend.list_tables()) == {
        "messages",
        "presets",
        "schema_migrations",
        "sessions",
        "user_configs",
        "users",
    }
    assert await backend.schema_version() == SCHEMA_VERSION


@pytest.mark.asyncio
async def test_user_session_message_crud(backend: SQLiteBackend) -> None:
    user = await backend.create_user(User(username="alice", default_model="mock"))
    assert user.id is not None
    assert (await backend.get_user(user.id)).username == "alice"
    assert (await backend.get_user_by_username("alice")).id == user.id

    user = await backend.update_user(user.model_copy(update={"default_model": "deepseek-chat"}))
    assert user.default_model == "deepseek-chat"
    assert len(await backend.list_users()) == 1

    session = await backend.create_session(Session(user_id=user.id, model_name="mock"))
    session = await backend.update_session(session.model_copy(update={"title": "SQLite 测试"}))
    assert (await backend.get_session(session.id)).title == "SQLite 测试"
    assert len(await backend.list_sessions(user.id)) == 1

    message = await backend.add_message(
        Message(session_id=session.id, role=MessageRole.HUMAN, content="你好")
    )
    message = await backend.update_message(message.model_copy(update={"content": "你好，SQLite"}))
    messages = await backend.list_messages(session.id)
    assert [item.content for item in messages] == ["你好，SQLite"]
    assert await backend.delete_message(message.id)
    assert await backend.list_messages(session.id) == []

    await backend.add_message(Message(session_id=session.id, role=MessageRole.AI, content="已保存"))
    assert await backend.delete_session(session.id)
    assert await backend.list_messages(session.id) == []
    assert await backend.delete_user(user.id)


@pytest.mark.asyncio
async def test_preset_and_user_config_crud(backend: SQLiteBackend) -> None:
    user = await backend.create_user(User(username="bob"))
    builtin = await backend.create_preset(
        Preset(name="通用助手", system_prompt="请清晰回答", is_builtin=True)
    )
    custom = await backend.create_preset(
        Preset(user_id=user.id, name="私人助手", system_prompt="请简洁回答")
    )
    visible = await backend.list_presets(user.id)
    assert {item.id for item in visible} == {builtin.id, custom.id}

    custom = await backend.update_preset(custom.model_copy(update={"description": "个人预设"}))
    assert custom.description == "个人预设"
    assert await backend.delete_preset(custom.id)

    saved = await backend.set_user_config(UserConfig(user_id=user.id, key="theme", value="dark"))
    assert saved.value == "dark"
    saved = await backend.set_user_config(saved.model_copy(update={"value": "light"}))
    assert (await backend.get_user_config(user.id, "theme")).value == "light"
    assert len(await backend.list_user_configs(user.id)) == 1
    assert await backend.delete_user_config(user.id, "theme")


def test_storage_factory_builds_sqlite_backend() -> None:
    project_root = Path.cwd().resolve()
    config = ProjectConfig(
        storage=StorageSection(type="sqlite", sqlite={"path": "data/test.db"})
    )
    backend = StorageFactory.create(config, project_root)
    assert isinstance(backend, SQLiteBackend)
    assert backend.database_path == (project_root / "data" / "test.db").resolve()
