from abc import ABC

import pytest
from pydantic import ValidationError

from config_manager import ConfigManager
from models.schemas import Message, MessageRole, Session, User
from storage.base import StorageBackend
from ui.tui.widgets import MAIN_MENU_ITEMS


def test_required_models_validate_data() -> None:
    user = User(id=1, username="  test_user  ")
    session = Session(id=1, user_id=user.id or 0)
    message = Message(session_id=session.id or 0, role=MessageRole.HUMAN, content="你好")

    assert user.username == "test_user"
    assert session.title == "新会话"
    assert message.role is MessageRole.HUMAN

    with pytest.raises(ValidationError):
        Message(session_id=1, role=MessageRole.HUMAN, content="   ")


def test_storage_backend_is_an_abstract_contract() -> None:
    assert issubclass(StorageBackend, ABC)
    assert StorageBackend.__abstractmethods__
    with pytest.raises(TypeError):
        StorageBackend()


def test_config_manager_loads_current_project() -> None:
    config = ConfigManager().load()
    assert config.app.name == "LLM Chat-bot"
    assert config.app.env in {"dev", "test", "prod"}
    assert config.storage.type == "sqlite"


def test_main_menu_contains_step2_entries() -> None:
    labels = [item.label for item in MAIN_MENU_ITEMS]
    assert labels[:5] == ["用户管理", "会话管理", "预设管理", "开始对话", "设置"]
    assert MAIN_MENU_ITEMS[-1].label == "退出"
