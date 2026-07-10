"""langchain-chat program entry point for the interactive Step 2 TUI."""

from __future__ import annotations

import argparse
import asyncio

from config_manager import ConfigManager
from ui.tui.app import TUIApplication


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="langchain-chat TUI")
    parser.add_argument(
        "--check",
        action="store_true",
        help="render the Step 2 menu once and exit without waiting for input",
    )
    return parser.parse_args()


async def run_application(check_only: bool = False) -> None:
    manager = ConfigManager()
    config = manager.load()
    app = TUIApplication(config, manager)
    if check_only:
        app.render_snapshot()
        app.show_message("Step 2 TUI 骨架验证通过。", title="MVP 检查")
        return
    await app.run()


def main() -> None:
    args = parse_args()
    asyncio.run(run_application(check_only=args.check))


if __name__ == "__main__":
    main()
