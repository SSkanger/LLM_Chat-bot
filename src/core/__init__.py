"""UI-independent business services."""

from core.user_manager import (
    DuplicateUsernameError,
    NoActiveUserError,
    UserManager,
    UserNotFoundError,
)
from core.preset_manager import (
    BuiltinPresetProtectedError,
    DuplicatePresetNameError,
    PresetManager,
    PresetNotFoundError,
)

__all__ = [
    "DuplicateUsernameError",
    "BuiltinPresetProtectedError",
    "DuplicatePresetNameError",
    "NoActiveUserError",
    "PresetManager",
    "PresetNotFoundError",
    "UserManager",
    "UserNotFoundError",
]
