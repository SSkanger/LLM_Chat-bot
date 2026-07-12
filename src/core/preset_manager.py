"""Built-in and user-owned Prompt preset management."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from core.user_manager import UserManager
from models.schemas import Preset
from storage.base import StorageBackend


class PresetManagerError(RuntimeError):
    """Base error for preset operations."""


class PresetNotFoundError(PresetManagerError):
    """Raised when a preset cannot be found or is not visible."""


class DuplicatePresetNameError(PresetManagerError):
    """Raised when a visible preset already uses a name."""


class BuiltinPresetProtectedError(PresetManagerError):
    """Raised when a built-in preset is modified or deleted."""


class PresetAccessDeniedError(PresetManagerError):
    """Raised when a user tries to manage another user's preset."""


class PresetManager:
    """Manage shared built-ins and isolated user presets."""

    def __init__(self, storage: StorageBackend, user_manager: UserManager) -> None:
        self.storage = storage
        self.user_manager = user_manager

    async def ensure_builtin_presets(self, definitions: Iterable[Mapping[str, Any]]) -> int:
        existing_names = {preset.name for preset in await self.storage.list_presets()}
        created = 0
        for definition in definitions:
            name = str(definition.get("name", "")).strip()
            system_prompt = str(definition.get("system_prompt", "")).strip()
            if not name or not system_prompt or name in existing_names:
                continue
            await self.storage.create_preset(
                Preset(
                    name=name,
                    description=str(definition.get("description", "")),
                    system_prompt=system_prompt,
                    is_builtin=True,
                )
            )
            existing_names.add(name)
            created += 1
        return created

    async def list_visible_presets(self) -> list[Preset]:
        user = self.user_manager.current_user
        return await self.storage.list_presets(user.id if user and user.id is not None else None)

    async def resolve_visible_preset(self, preset_id: int | str) -> Preset:
        try:
            numeric_id = int(str(preset_id).strip())
        except ValueError as exc:
            raise PresetNotFoundError(f"无效的预设 ID：{preset_id}") from exc
        preset = await self.storage.get_preset(numeric_id)
        if preset is None:
            raise PresetNotFoundError(f"找不到预设：{preset_id}")
        user = self.user_manager.current_user
        if preset.user_id is not None and (user is None or preset.user_id != user.id):
            raise PresetNotFoundError(f"找不到预设：{preset_id}")
        return preset

    async def create_custom_preset(
        self, name: str, description: str, system_prompt: str
    ) -> Preset:
        user = self.user_manager.require_current_user()
        normalized_name = name.strip()
        normalized_prompt = system_prompt.strip()
        if not normalized_name:
            raise ValueError("预设名称不能为空")
        if not normalized_prompt:
            raise ValueError("System Prompt 不能为空")
        await self._ensure_unique_name(normalized_name)
        return await self.storage.create_preset(
            Preset(
                user_id=user.id,
                name=normalized_name,
                description=description.strip(),
                system_prompt=normalized_prompt,
                is_builtin=False,
            )
        )

    async def update_custom_preset(
        self,
        preset_id: int | str,
        *,
        name: str | None = None,
        description: str | None = None,
        system_prompt: str | None = None,
    ) -> Preset:
        preset = await self.resolve_visible_preset(preset_id)
        self._require_custom_owner(preset)
        updates: dict[str, Any] = {}
        if name is not None and name.strip():
            normalized_name = name.strip()
            await self._ensure_unique_name(normalized_name, exclude_id=preset.id)
            updates["name"] = normalized_name
        if description is not None:
            updates["description"] = description.strip()
        if system_prompt is not None and system_prompt.strip():
            updates["system_prompt"] = system_prompt.strip()
        return await self.storage.update_preset(preset.model_copy(update=updates))

    async def delete_custom_preset(self, preset_id: int | str) -> Preset:
        preset = await self.resolve_visible_preset(preset_id)
        self._require_custom_owner(preset)
        if preset.id is None or not await self.storage.delete_preset(preset.id):
            raise PresetNotFoundError(f"找不到预设：{preset_id}")
        user = self.user_manager.require_current_user()
        if user.default_preset_id == preset.id:
            self.user_manager.current_user = await self.storage.update_user(
                user.model_copy(update={"default_preset_id": None})
            )
        return preset

    async def select_preset(self, preset_id: int | str | None) -> Preset | None:
        user = self.user_manager.require_current_user()
        preset = None if preset_id is None else await self.resolve_visible_preset(preset_id)
        self.user_manager.current_user = await self.storage.update_user(
            user.model_copy(update={"default_preset_id": preset.id if preset else None})
        )
        return preset

    async def get_selected_preset(self) -> Preset | None:
        user = self.user_manager.current_user
        if user is None or user.default_preset_id is None:
            return None
        preset = await self.storage.get_preset(user.default_preset_id)
        if preset is None:
            self.user_manager.current_user = await self.storage.update_user(
                user.model_copy(update={"default_preset_id": None})
            )
        return preset

    async def _ensure_unique_name(self, name: str, exclude_id: int | None = None) -> None:
        for preset in await self.list_visible_presets():
            if preset.name == name and preset.id != exclude_id:
                raise DuplicatePresetNameError(f"预设名称“{name}”已存在")

    def _require_custom_owner(self, preset: Preset) -> None:
        if preset.is_builtin or preset.user_id is None:
            raise BuiltinPresetProtectedError("系统内置预设不可编辑或删除")
        user = self.user_manager.require_current_user()
        if preset.user_id != user.id:
            raise PresetAccessDeniedError("不能管理其他用户的预设")
