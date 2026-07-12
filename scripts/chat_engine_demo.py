"""Run the Step 6 chat engine without starting a UI."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config_manager import ConfigManager  # noqa: E402
from core.chat_engine import ChatEngine  # noqa: E402


async def stream_turn(engine: ChatEngine, message: str) -> None:
    print(f"\n用户：{message}")
    print("助手：", end="", flush=True)
    async for chunk in engine.astream(message):
        print(chunk, end="", flush=True)
    usage = engine.last_usage
    print(
        f"\nToken：prompt={usage.prompt_tokens}, "
        f"completion={usage.completion_tokens}, total={usage.total_tokens}"
    )


async def main() -> None:
    manager = ConfigManager(PROJECT_ROOT)
    config = manager.load()
    if manager.environment is None:
        raise RuntimeError("环境配置未加载")
    engine = ChatEngine.from_config(
        config,
        manager.environment,
        system_prompt="你是一个清晰、友好的中文助手。",
    )
    print(f"模型：{engine.model_name}")
    await stream_turn(engine, "请记住我的课程项目叫 langchain-chat")
    await stream_turn(engine, "我的课程项目叫什么？")
    total = engine.total_usage
    print(
        f"\n累计 Token：prompt={total.prompt_tokens}, "
        f"completion={total.completion_tokens}, total={total.total_tokens}"
    )
    print(f"历史消息：{len(engine.history_messages())} 条")
    print("[完成] Step 6 多轮流式对话引擎验证通过")


if __name__ == "__main__":
    asyncio.run(main())
