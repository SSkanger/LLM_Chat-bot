"""UI protocol implemented by terminal and future web interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence


class AbstractUI(ABC):
    """Behavior required from every user interface implementation."""

    @abstractmethod
    async def run(self) -> None:
        """Start the interface event loop."""

    @abstractmethod
    def show_message(self, message: str, *, title: str = "提示") -> None:
        """Display an informational message."""

    @abstractmethod
    def show_error(self, message: str) -> None:
        """Display an error message."""

    @abstractmethod
    def show_markdown(self, content: str) -> None:
        """Render Markdown content."""

    @abstractmethod
    async def prompt(self, message: str, *, multiline: bool = False) -> str:
        """Collect text input from the user."""

    @abstractmethod
    async def select(self, message: str, choices: Sequence[str]) -> str:
        """Ask the user to choose one item."""
