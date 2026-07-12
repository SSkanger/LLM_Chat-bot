"""Interactive terminal application with Step 5 preset management."""

from __future__ import annotations

from collections.abc import Sequence

from prompt_toolkit import PromptSession
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from config_manager import ConfigManager, ProjectConfig
from core.preset_manager import PresetManager, PresetManagerError
from core.user_manager import UserManager, UserManagerError
from interface.ui_protocol import AbstractUI
from storage.base import StorageBackend
from ui.tui.chat_view import ChatView
from ui.tui.menu_view import MenuView
from ui.tui.widgets import TUIWidgets


class TUIApplication(AbstractUI):
    def __init__(
        self,
        config: ProjectConfig,
        config_manager: ConfigManager,
        storage: StorageBackend,
        console: Console | None = None,
    ) -> None:
        self.config = config
        self.config_manager = config_manager
        self.storage = storage
        self.user_manager = UserManager(storage, config.llm.default_model)
        self.preset_manager = PresetManager(storage, self.user_manager)
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
        current_username = (
            self.user_manager.current_user.username if self.user_manager.current_user else "未选择"
        )
        self.widgets.render_header(
            self.config.app.name,
            self.config.app.version,
            self.config.app.env,
            current_username,
        )
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
        if choice == "1":
            await self._user_management_loop()
            return
        if choice == "3":
            await self._preset_management_loop()
            return
        if choice == "4":
            self.chat.render_stub()
        elif choice == "5":
            self._show_settings()
        else:
            titles = {"2": "会话管理"}
            title = titles.get(choice, "功能")
            self.show_message(f"{title}入口已建立，业务功能将在后续对应步骤实现。", title=title)
        await self._pause()

    def _show_settings(self) -> None:
        current_user = (
            self.user_manager.current_user.username if self.user_manager.current_user else "未选择"
        )
        message = (
            f"运行环境：{self.config.app.env}\n"
            f"当前用户：{current_user}\n"
            f"默认模型：{self.config.llm.default_model}\n"
            f"存储后端：{self.config.storage.type}\n"
            f"内置预设：{len(self.config_manager.load_presets())} 个"
        )
        self.show_message(message, title="设置")

    async def _preset_management_loop(self) -> None:
        while self.running:
            self.console.clear()
            current_username = (
                self.user_manager.current_user.username if self.user_manager.current_user else "未选择"
            )
            self.widgets.render_header(
                self.config.app.name,
                self.config.app.version,
                self.config.app.env,
                current_username,
            )
            presets = await self.preset_manager.list_visible_presets()
            selected = await self.preset_manager.get_selected_preset()
            self.menu.render_preset_menu(
                presets,
                selected,
                has_user=self.user_manager.current_user is not None,
            )
            action = await self.menu.choose_preset_action()
            if action == "0":
                return
            if self.user_manager.current_user is None:
                self.show_error("请先创建或切换用户")
                await self._pause()
                continue
            try:
                if action == "1":
                    await self._create_preset()
                elif action == "2":
                    await self._edit_preset()
                elif action == "3":
                    await self._delete_preset()
                elif action == "4":
                    await self._select_preset()
                elif action == "5":
                    await self.preset_manager.select_preset(None)
                    self.show_message("当前会话角色已设为不使用预设。", title="预设选择")
            except (PresetManagerError, UserManagerError, ValueError) as exc:
                self.show_error(str(exc))
            await self._pause()

    async def _create_preset(self) -> None:
        name = await self.prompt("预设名称 > ")
        description = await self.prompt("预设说明 > ")
        system_prompt = await self.prompt("System Prompt > ")
        preset = await self.preset_manager.create_custom_preset(name, description, system_prompt)
        self.show_message(f"个人预设“{preset.name}”创建成功。", title="新增预设")

    async def _edit_preset(self) -> None:
        preset_id = await self.prompt("请输入要编辑的个人预设 ID > ")
        preset = await self.preset_manager.resolve_visible_preset(preset_id)
        name = await self.prompt(f"名称（回车保留“{preset.name}”）> ")
        description = await self.prompt("说明（回车保留原值）> ")
        system_prompt = await self.prompt("System Prompt（回车保留原值）> ")
        updated = await self.preset_manager.update_custom_preset(
            preset_id,
            name=name or None,
            description=description if description else None,
            system_prompt=system_prompt or None,
        )
        self.show_message(f"个人预设“{updated.name}”已更新。", title="编辑预设")

    async def _delete_preset(self) -> None:
        preset_id = await self.prompt("请输入要删除的个人预设 ID > ")
        preset = await self.preset_manager.resolve_visible_preset(preset_id)
        confirmation = await self.select(f"确认删除预设“{preset.name}”吗", ("是", "否"))
        if confirmation != "是":
            self.show_message("已取消删除。", title="删除预设")
            return
        deleted = await self.preset_manager.delete_custom_preset(preset_id)
        self.show_message(f"个人预设“{deleted.name}”已删除。", title="删除预设")

    async def _select_preset(self) -> None:
        preset_id = await self.prompt("请输入要使用的预设 ID > ")
        selected = await self.preset_manager.select_preset(preset_id)
        self.show_message(f"已选择预设“{selected.name}”。", title="预设选择")

    async def _user_management_loop(self) -> None:
        while self.running:
            self.console.clear()
            current_username = (
                self.user_manager.current_user.username if self.user_manager.current_user else "未选择"
            )
            self.widgets.render_header(
                self.config.app.name,
                self.config.app.version,
                self.config.app.env,
                current_username,
            )
            users = await self.user_manager.list_users()
            self.menu.render_user_menu(users, self.user_manager.current_user)
            action = await self.menu.choose_user_action()
            if action == "0":
                return
            try:
                if action == "1":
                    await self._create_user()
                elif action == "2":
                    await self._switch_user()
                elif action == "3":
                    await self._delete_user()
            except (UserManagerError, ValueError) as exc:
                self.show_error(str(exc))
            await self._pause()

    async def _create_user(self) -> None:
        username = (await self.prompt("请输入新用户名 > ")).strip()
        user = await self.user_manager.create_user(username)
        self.show_message(f"用户“{user.username}”创建成功。", title="创建用户")

    async def _switch_user(self) -> None:
        identifier = (await self.prompt("请输入用户 ID 或用户名 > ")).strip()
        user = await self.user_manager.switch_user(identifier)
        sessions = await self.user_manager.list_current_user_sessions()
        self.show_message(
            f"已切换到“{user.username}”，该用户当前有 {len(sessions)} 个会话。",
            title="切换用户",
        )

    async def _delete_user(self) -> None:
        identifier = (await self.prompt("请输入要删除的用户 ID 或用户名 > ")).strip()
        user = await self.user_manager.resolve_user(identifier)
        confirmation = await self.select(
            f"删除“{user.username}”及其全部会话、消息、预设和配置，确认吗",
            ("是", "否"),
        )
        if confirmation != "是":
            self.show_message("已取消删除。", title="删除用户")
            return
        deleted = await self.user_manager.delete_user(user.id or identifier)
        self.show_message(f"用户“{deleted.username}”及关联数据已删除。", title="删除用户")

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
