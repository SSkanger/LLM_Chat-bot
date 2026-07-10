"""Main menu rendering and selection."""

from __future__ import annotations

from rich.table import Table

from models.schemas import User
from ui.tui.widgets import MAIN_MENU_ITEMS, MenuItem, TUIWidgets


USER_MENU_ITEMS: tuple[MenuItem, ...] = (
    MenuItem("1", "创建用户", "创建唯一用户名并保存到 SQLite"),
    MenuItem("2", "切换用户", "切换当前用户并加载其隔离数据"),
    MenuItem("3", "删除用户", "二次确认后删除用户及全部关联数据"),
    MenuItem("0", "返回主菜单", "返回"),
)


class MenuView:
    def __init__(self, widgets: TUIWidgets) -> None:
        self.widgets = widgets

    def render(self) -> None:
        self.widgets.render_menu(MAIN_MENU_ITEMS)

    async def choose(self) -> str:
        return await self.widgets.ask_menu(MAIN_MENU_ITEMS)

    def render_user_menu(self, users: list[User], current_user: User | None) -> None:
        table = Table(title="用户列表", show_header=True, header_style="bold")
        table.add_column("当前", justify="center", width=6)
        table.add_column("ID", justify="right", width=6)
        table.add_column("用户名", width=24)
        table.add_column("默认模型")
        if users:
            for user in users:
                marker = "*" if current_user and current_user.id == user.id else ""
                table.add_row(marker, str(user.id), user.username, user.default_model)
        else:
            table.add_row("", "-", "暂无用户", "-")
        self.widgets.console.print(table)
        self.widgets.render_menu(USER_MENU_ITEMS)

    async def choose_user_action(self) -> str:
        return await self.widgets.ask_menu(USER_MENU_ITEMS)
