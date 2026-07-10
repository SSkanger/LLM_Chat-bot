"""Factory for selecting a storage backend from validated configuration."""

from __future__ import annotations

from pathlib import Path

from config_manager import PROJECT_ROOT, ProjectConfig
from storage.base import StorageBackend
from storage.sqlite_backend import SQLiteBackend


class StorageFactory:
    """Create storage implementations without coupling callers to classes."""

    @staticmethod
    def create(config: ProjectConfig, project_root: Path | None = None) -> StorageBackend:
        backend_type = config.storage.type.strip().lower()
        root = (project_root or PROJECT_ROOT).resolve()
        if backend_type == "sqlite":
            configured_path = config.storage.sqlite.get("path", "data/sqlite/app.db")
            path = Path(str(configured_path))
            if not path.is_absolute():
                path = root / path
            return SQLiteBackend(path)
        if backend_type in {"mysql", "file"}:
            raise NotImplementedError(f"{backend_type} 存储后端将在后续步骤实现")
        raise ValueError(f"不支持的存储后端：{backend_type}")
