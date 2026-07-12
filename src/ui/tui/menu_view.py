"""Main menu rendering and selection."""

from __future__ import annotations

from rich.table import Table

from models.schemas import Preset, User
from ui.tui.widgets import MAIN_MENU_ITEMS, MenuItem, TUIWidgets


USER_MENU_ITEMS: tuple[MenuItem, ...] = (
    MenuItem("1", "创建用户", "创建唯一用户名并保存到 SQLite"),
    MenuItem("2", "切换用户", "切换当前用户并加载其隔离数据"),
    MenuItem("3", "删除用户", "二次确认后删除用户及全部关联数据"),
    MenuItem("0", "返回主菜单", "返回"),
)

PRESET_MENU_ITEMS: tuple[MenuItem, ...] = (
    MenuItem("1", "新增个人预设", "创建当前用户专属 Prompt"),
    MenuItem("2", "编辑个人预设", "修改名称、说明或 System Prompt"),
    MenuItem("3", "删除个人预设", "二次确认后删除"),
    MenuItem("4", "选择预设", "设为当前用户默认预设"),
    MenuItem("5", "不使用预设", "清除当前选择"),
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

    def render_preset_menu(
        self, presets: list[Preset], selected_preset: Preset | None, has_user: bool
    ) -> None:
        table = Table(title="预设 Prompt", show_header=True, header_style="bold")
        table.add_column("当前", justify="center", width=6)
        table.add_column("ID", justify="right", width=6)
        table.add_column("类型", width=8)
        table.add_column("名称", width=18)
        table.add_column("说明")
        if presets:
            for preset in presets:
                marker = "*" if selected_preset and selected_preset.id == preset.id else ""
                preset_type = "系统" if preset.is_builtin else "个人"
                table.add_row(marker, str(preset.id), preset_type, preset.name, preset.description)
        else:
            table.add_row("", "-", "-", "暂无预设", "-")
        self.widgets.console.print(table)
        if not has_user:
            self.widgets.console.print("[yellow]请先在用户管理中创建或切换用户。[/yellow]")
        self.widgets.render_menu(PRESET_MENU_ITEMS)

    async def choose_preset_action(self) -> str:
        return await self.widgets.ask_menu(PRESET_MENU_ITEMS)
