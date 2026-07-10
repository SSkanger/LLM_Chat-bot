from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio

from core.user_manager import (
    DuplicateUsernameError,
    NoActiveUserError,
    UserManager,
    UserNotFoundError,
)
from models.schemas import Message, MessageRole, Preset, Session, UserConfig
from storage.sqlite_backend import SQLiteBackend
from ui.tui.menu_view import USER_MENU_ITEMS


@pytest_asyncio.fixture
async def user_context():
    database_path = Path("data/test") / f"step4-{uuid4().hex}.db"
    storage = SQLiteBackend(database_path)
    await storage.initialize()
    manager = UserManager(storage, default_model="mock")
    try:
        yield storage, manager
    finally:
        await storage.close()
        for candidate in (
            storage.database_path,
            Path(f"{storage.database_path}-wal"),
            Path(f"{storage.database_path}-shm"),
        ):
            candidate.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_create_switch_and_persist_users(user_context) -> None:
    storage, manager = user_context
    alice = await manager.create_user("  alice  ")
    bob = await manager.create_user("bob", default_model="deepseek-chat")

    assert manager.current_user.id == alice.id
    assert [user.username for user in await manager.list_users()] == ["alice", "bob"]
    assert (await manager.switch_user("bob")).id == bob.id

    reloaded_manager = UserManager(storage)
    assert (await reloaded_manager.switch_user(alice.id)).username == "alice"


@pytest.mark.asyncio
async def test_unique_username_and_missing_user_errors(user_context) -> None:
    _, manager = user_context
    await manager.create_user("alice")
    with pytest.raises(DuplicateUsernameError):
        await manager.create_user("alice")
    with pytest.raises(UserNotFoundError):
        await manager.switch_user("missing")


@pytest.mark.asyncio
async def test_user_data_isolation(user_context) -> None:
    storage, manager = user_context
    alice = await manager.create_user("alice")
    bob = await manager.create_user("bob")

    alice_session = await storage.create_session(Session(user_id=alice.id, title="Alice 会话"))
    await storage.add_message(
        Message(session_id=alice_session.id, role=MessageRole.HUMAN, content="Alice 私有消息")
    )
    bob_session = await storage.create_session(Session(user_id=bob.id, title="Bob 会话"))
    await storage.add_message(
        Message(session_id=bob_session.id, role=MessageRole.HUMAN, content="Bob 私有消息")
    )
    await storage.create_preset(
        Preset(user_id=alice.id, name="Alice 预设", system_prompt="Alice only")
    )
    await storage.create_preset(Preset(user_id=bob.id, name="Bob 预设", system_prompt="Bob only"))
    await storage.set_user_config(UserConfig(user_id=alice.id, key="theme", value="alice"))
    await storage.set_user_config(UserConfig(user_id=bob.id, key="theme", value="bob"))

    await manager.switch_user(alice.id)
    assert [session.title for session in await manager.list_current_user_sessions()] == ["Alice 会话"]
    assert {preset.name for preset in await manager.list_current_user_presets()} == {"Alice 预设"}
    assert [item.value for item in await manager.list_current_user_configs()] == ["alice"]

    await manager.switch_user(bob.id)
    assert [session.title for session in await manager.list_current_user_sessions()] == ["Bob 会话"]
    assert {preset.name for preset in await manager.list_current_user_presets()} == {"Bob 预设"}
    assert [item.value for item in await manager.list_current_user_configs()] == ["bob"]


@pytest.mark.asyncio
async def test_delete_user_cascades_and_clears_active_context(user_context) -> None:
    storage, manager = user_context
    user = await manager.create_user("delete_me")
    session = await storage.create_session(Session(user_id=user.id))
    await storage.add_message(
        Message(session_id=session.id, role=MessageRole.HUMAN, content="需要级联删除")
    )
    await storage.create_preset(
        Preset(user_id=user.id, name="待删除预设", system_prompt="delete")
    )
    await storage.set_user_config(UserConfig(user_id=user.id, key="delete", value="yes"))

    await manager.delete_user(user.id)
    assert manager.current_user is None
    assert await storage.get_user(user.id) is None
    assert await storage.get_session(session.id) is None
    assert await storage.list_messages(session.id) == []
    with pytest.raises(NoActiveUserError):
        await manager.list_current_user_sessions()


def test_tui_user_menu_contains_required_actions() -> None:
    assert [item.label for item in USER_MENU_ITEMS] == [
        "创建用户",
        "切换用户",
        "删除用户",
        "返回主菜单",
    ]
