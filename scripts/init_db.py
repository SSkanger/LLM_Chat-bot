"""Initialize the configured database and seed built-in presets."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config_manager import ConfigManager  # noqa: E402
from models.schemas import Preset  # noqa: E402
from storage.factory import StorageFactory  # noqa: E402
from storage.sqlite_backend import SQLiteBackend  # noqa: E402


async def seed_builtin_presets(backend: SQLiteBackend, manager: ConfigManager) -> int:
    existing_names = {preset.name for preset in await backend.list_presets()}
    created = 0
    for item in manager.load_presets():
        name = str(item.get("name", "")).strip()
        if not name or name in existing_names:
            continue
        await backend.create_preset(
            Preset(
                name=name,
                description=str(item.get("description", "")),
                system_prompt=str(item.get("system_prompt", "")),
                is_builtin=True,
            )
        )
        existing_names.add(name)
        created += 1
    return created


async def initialize_database() -> None:
    manager = ConfigManager(PROJECT_ROOT)
    config = manager.load()
    backend = StorageFactory.create(config, PROJECT_ROOT)
    if not isinstance(backend, SQLiteBackend):
        raise RuntimeError("Step 3 初始化脚本当前仅支持 SQLite")

    try:
        await backend.initialize()
        seeded = await seed_builtin_presets(backend, manager)
        tables = await backend.list_tables()
        version = await backend.schema_version()
        print("=" * 72)
        print("langchain-chat 数据库初始化完成")
        print(f"数据库路径：{backend.database_path}")
        print(f"迁移版本：{version}")
        print(f"数据表：{', '.join(tables)}")
        print(f"新增内置预设：{seeded}")
        print("[完成] Step 3 SQLite 后端与数据库初始化验证通过")
        print("=" * 72)
    finally:
        await backend.close()


if __name__ == "__main__":
    asyncio.run(initialize_database())
