from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio

from core.preset_manager import (
    BuiltinPresetProtectedError,
    DuplicatePresetNameError,
    PresetManager,
    PresetNotFoundError,
)
from core.user_manager import UserManager
from storage.sqlite_backend import SQLiteBackend
from ui.tui.menu_view import PRESET_MENU_ITEMS


BUILTINS = [
    {"name": "翻译助手", "description": "中英互译", "system_prompt": "请负责翻译"},
    {"name": "代码专家", "description": "代码帮助", "system_prompt": "请检查代码"},
]


@pytest_asyncio.fixture
async def preset_context():
    database_path = Path("data/test") / f"step5-{uuid4().hex}.db"
    storage = SQLiteBackend(database_path)
    await storage.initialize()
    users = UserManager(storage, default_model="mock")
    presets = PresetManager(storage, users)
    try:
        yield storage, users, presets
    finally:
        await storage.close()
        for candidate in (
            storage.database_path,
            Path(f"{storage.database_path}-wal"),
            Path(f"{storage.database_path}-shm"),
        ):
            candidate.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_builtin_presets_are_shared_and_seeded_once(preset_context) -> None:
    _, users, presets = preset_context
    assert await presets.ensure_builtin_presets(BUILTINS) == 2
    assert await presets.ensure_builtin_presets(BUILTINS) == 0
    assert [item.name for item in await presets.list_visible_presets()] == ["代码专家", "翻译助手"]

    await users.create_user("alice")
    assert {item.name for item in await presets.list_visible_presets()} == {"翻译助手", "代码专家"}


@pytest.mark.asyncio
async def test_custom_preset_crud_and_protection(preset_context) -> None:
    _, users, presets = preset_context
    await presets.ensure_builtin_presets(BUILTINS)
    await users.create_user("alice")
    custom = await presets.create_custom_preset("论文助手", "帮助论文", "请使用学术语言")
    custom = await presets.update_custom_preset(
        custom.id,
        name="学术助手",
        description="学术写作",
        system_prompt="请严谨回答",
    )
    assert custom.name == "学术助手"
    assert custom.system_prompt == "请严谨回答"

    with pytest.raises(DuplicatePresetNameError):
        await presets.create_custom_preset("翻译助手", "重复", "重复")
    builtin = next(item for item in await presets.list_visible_presets() if item.is_builtin)
    with pytest.raises(BuiltinPresetProtectedError):
        await presets.update_custom_preset(builtin.id, name="不能修改")
    with pytest.raises(BuiltinPresetProtectedError):
        await presets.delete_custom_preset(builtin.id)

    assert (await presets.delete_custom_preset(custom.id)).name == "学术助手"


@pytest.mark.asyncio
async def test_user_presets_are_isolated(preset_context) -> None:
    _, users, presets = preset_context
    alice = await users.create_user("alice")
    alice_preset = await presets.create_custom_preset("Alice 私有", "", "Alice only")
    bob = await users.create_user("bob")
    await users.switch_user(bob.id)
    bob_preset = await presets.create_custom_preset("Bob 私有", "", "Bob only")

    assert {item.name for item in await presets.list_visible_presets()} == {"Bob 私有"}
    with pytest.raises(PresetNotFoundError):
        await presets.resolve_visible_preset(alice_preset.id)

    await users.switch_user(alice.id)
    assert {item.name for item in await presets.list_visible_presets()} == {"Alice 私有"}
    with pytest.raises(PresetNotFoundError):
        await presets.resolve_visible_preset(bob_preset.id)


@pytest.mark.asyncio
async def test_select_and_clear_preset_persists_on_user(preset_context) -> None:
    storage, users, presets = preset_context
    await presets.ensure_builtin_presets(BUILTINS)
    user = await users.create_user("alice")
    selected = (await presets.list_visible_presets())[0]

    await presets.select_preset(selected.id)
    assert (await presets.get_selected_preset()).id == selected.id
    assert (await storage.get_user(user.id)).default_preset_id == selected.id

    await presets.select_preset(None)
    assert await presets.get_selected_preset() is None
    assert (await storage.get_user(user.id)).default_preset_id is None


def test_tui_preset_menu_contains_required_actions() -> None:
    assert [item.label for item in PRESET_MENU_ITEMS] == [
        "新增个人预设",
        "编辑个人预设",
        "删除个人预设",
        "选择预设",
        "不使用预设",
        "返回主菜单",
    ]
