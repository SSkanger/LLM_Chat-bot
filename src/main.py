"""langchain-chat program entry point for the interactive Step 5 TUI."""

from __future__ import annotations

import argparse
import asyncio

from config_manager import ConfigManager
from storage.factory import StorageFactory
from ui.tui.app import TUIApplication


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="langchain-chat TUI")
    parser.add_argument(
        "--check",
        action="store_true",
        help="render the current menu once and exit without waiting for input",
    )
    return parser.parse_args()


async def run_application(check_only: bool = False) -> None:
    manager = ConfigManager()
    config = manager.load()
    storage = StorageFactory.create(config)
    await storage.initialize()
    try:
        app = TUIApplication(config, manager, storage)
        await app.preset_manager.ensure_builtin_presets(manager.load_presets())
        if check_only:
            app.render_snapshot()
            app.show_message("Step 5 预设管理与 TUI 路由加载正常。", title="MVP 检查")
            return
        await app.run()
    finally:
        await storage.close()


def main() -> None:
    args = parse_args()
    asyncio.run(run_application(check_only=args.check))


if __name__ == "__main__":
    main()
