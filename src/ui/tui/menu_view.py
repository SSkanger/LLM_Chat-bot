"""Main menu rendering and selection."""

from __future__ import annotations

from ui.tui.widgets import MAIN_MENU_ITEMS, TUIWidgets


class MenuView:
    def __init__(self, widgets: TUIWidgets) -> None:
        self.widgets = widgets

    def render(self) -> None:
        self.widgets.render_menu(MAIN_MENU_ITEMS)

    async def choose(self) -> str:
        return await self.widgets.ask_menu(MAIN_MENU_ITEMS)
