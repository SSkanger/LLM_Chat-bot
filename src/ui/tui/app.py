"""Interactive terminal application skeleton for Step 2."""

from __future__ import annotations

from collections.abc import Sequence

from prompt_toolkit import PromptSession
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from config_manager import ConfigManager, ProjectConfig
from interface.ui_protocol import AbstractUI
from ui.tui.chat_view import ChatView
from ui.tui.menu_view import MenuView
from ui.tui.widgets import TUIWidgets


class TUIApplication(AbstractUI):
    def __init__(
        self,
        config: ProjectConfig,
        config_manager: ConfigManager,
        console: Console | None = None,
    ) -> None:
        self.config = config
        self.config_manager = config_manager
        self.widgets = TUIWidgets(console)
        self.console = self.widgets.console
        self.menu = MenuView(self.widgets)
        self.chat = ChatView(self.console)
        self._input_session: PromptSession[str] | None = None
        self.running = False

    @property
    def input_session(self) -> PromptSession[str]:
        """Create prompt_toolkit state lazily for non-interactive MVP checks."""
        if self._input_session is None:
            self._input_session = PromptSession()
        return self._input_session

    def render_snapshot(self) -> None:
        self.widgets.render_header(self.config.app.name, self.config.app.version, self.config.app.env)
        self.menu.render()

    async def run(self) -> None:
        self.running = True
        while self.running:
            self.console.clear()
            self.render_snapshot()
            choice = await self.menu.choose()
            await self._dispatch(choice)

    async def _dispatch(self, choice: str) -> None:
        if choice == "0":
            self.running = False
            self.show_message("已退出 langchain-chat。", title="再见")
            return
        if choice == "4":
            self.chat.render_stub()
        elif choice == "5":
            self._show_settings()
        else:
            titles = {"1": "用户管理", "2": "会话管理", "3": "预设管理"}
            title = titles.get(choice, "功能")
            self.show_message(f"{title}入口已建立，业务功能将在后续对应步骤实现。", title=title)
        await self._pause()

    def _show_settings(self) -> None:
        message = (
            f"运行环境：{self.config.app.env}\n"
            f"默认模型：{self.config.llm.default_model}\n"
            f"存储后端：{self.config.storage.type}\n"
            f"内置预设：{len(self.config_manager.load_presets())} 个"
        )
        self.show_message(message, title="设置")

    async def _pause(self) -> None:
        try:
            await self.input_session.prompt_async("按 Enter 返回主菜单...")
        except (EOFError, KeyboardInterrupt):
            self.running = False

    def show_message(self, message: str, *, title: str = "提示") -> None:
        self.console.print(Panel(message, title=title, border_style="green"))

    def show_error(self, message: str) -> None:
        self.console.print(Panel(message, title="错误", border_style="red"))

    def show_markdown(self, content: str) -> None:
        self.console.print(Markdown(content))

    async def prompt(self, message: str, *, multiline: bool = False) -> str:
        return await self.input_session.prompt_async(message, multiline=multiline)

    async def select(self, message: str, choices: Sequence[str]) -> str:
        while True:
            answer = (await self.input_session.prompt_async(f"{message} ({'/'.join(choices)}) > ")).strip()
            if answer in choices:
                return answer
            self.show_error("输入不在可选项中。")
