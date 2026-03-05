"""
FuviAI Marketing Agent — Conversation Memory
Quản lý conversation history với sliding window
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger


@dataclass
class Message:
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


class ConversationMemory:
    """
    Quản lý conversation history với sliding window.
    Tự động trim khi vượt quá max_messages để tránh context quá dài.
    """

    def __init__(self, max_messages: int = 20, session_id: str = "default"):
        self.session_id = session_id
        self.max_messages = max_messages
        self._messages: list[Message] = []

    def add(self, role: str, content: str) -> None:
        self._messages.append(Message(role=role, content=content))
        if len(self._messages) > self.max_messages:
            # Giữ lại system context, xoá cặp tin nhắn cũ nhất
            self._messages = self._messages[-self.max_messages:]
            logger.debug(f"Memory trimmed to {self.max_messages} messages")

    def to_anthropic_format(self) -> list[dict]:
        """Chuyển sang format messages[] của Anthropic API."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self._messages
        ]

    def clear(self) -> None:
        self._messages = []
        logger.debug(f"Memory cleared | session={self.session_id}")

    @property
    def message_count(self) -> int:
        return len(self._messages)

    def get_last_n(self, n: int) -> list[Message]:
        return self._messages[-n:]

    def __repr__(self) -> str:
        return f"ConversationMemory(session={self.session_id}, messages={self.message_count})"
