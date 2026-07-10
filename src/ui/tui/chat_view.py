"""Chat view placeholder for the Step 2 skeleton."""

from rich.console import Console
from rich.panel import Panel


class ChatView:
    def __init__(self, console: Console) -> None:
        self.console = console

    def render_stub(self) -> None:
        self.console.print(
            Panel(
                "对话引擎将在 Step 6 实现，并于 Step 7 接入真实多轮流式对话。",
                title="开始对话",
                border_style="blue",
            )
        )
