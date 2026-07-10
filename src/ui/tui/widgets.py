"""Reusable Rich renderers and prompt_toolkit input helpers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


@dataclass(frozen=True)
class MenuItem:
    key: str
    label: str
    description: str


MAIN_MENU_ITEMS: tuple[MenuItem, ...] = (
    MenuItem("1", "用户管理", "创建、切换和管理用户（Step 4 实现）"),
    MenuItem("2", "会话管理", "浏览和管理历史会话（Step 8 实现）"),
    MenuItem("3", "预设管理", "查看和选择 Prompt 角色（Step 5 实现）"),
    MenuItem("4", "开始对话", "进入多轮流式对话（Step 7 实现）"),
    MenuItem("5", "设置", "查看模型、存储和运行环境"),
    MenuItem("0", "退出", "结束程序"),
)


class TUIWidgets:
    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self._session: PromptSession[str] | None = None

    @property
    def session(self) -> PromptSession[str]:
        """Create the terminal input session only when interaction starts."""
        if self._session is None:
            self._session = PromptSession(history=InMemoryHistory())
        return self._session

    def render_header(self, app_name: str, version: str, environment: str) -> None:
        subtitle = f"v{version} | 环境: {environment} | Step 3"
        self.console.print(Panel.fit(f"[bold cyan]{app_name}[/bold cyan]\n{subtitle}", border_style="cyan"))

    def render_menu(self, items: Sequence[MenuItem] = MAIN_MENU_ITEMS) -> None:
        table = Table(title="主菜单", show_header=True, header_style="bold")
        table.add_column("按键", justify="center", width=6)
        table.add_column("功能", width=16)
        table.add_column("说明")
        for item in items:
            table.add_row(item.key, item.label, item.description)
        self.console.print(table)

    async def ask_menu(self, items: Sequence[MenuItem] = MAIN_MENU_ITEMS) -> str:
        choices = [item.key for item in items] + [item.label for item in items]
        completer = WordCompleter(choices, ignore_case=True)
        while True:
            try:
                answer = (await self.session.prompt_async("请选择功能 > ", completer=completer)).strip()
            except (EOFError, KeyboardInterrupt):
                return "0"
            for item in items:
                if answer in {item.key, item.label}:
                    return item.key
            self.console.print("[yellow]请输入菜单编号或功能名称。[/yellow]")
