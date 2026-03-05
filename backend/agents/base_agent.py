"""
FuviAI Marketing Agent — Base Agent
Base class kết nối Claude API, dùng chung cho tất cả agents
"""

from __future__ import annotations

import time
from typing import AsyncIterator, Iterator
from loguru import logger

import anthropic
from backend.config.settings import get_settings
from backend.config.prompts_vn import FUVIAI_SYSTEM_PROMPT


class BaseAgent:
    """
    Base class cho tất cả FuviAI agents.

    Usage:
        agent = BaseAgent(system_prompt="...")
        response = agent.chat("Viết caption Facebook cho sản phẩm X")
    """

    def __init__(
        self,
        system_prompt: str = FUVIAI_SYSTEM_PROMPT,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ):
        self.settings = get_settings()
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.conversation_history: list[dict] = []

        self._client = anthropic.Anthropic(
            api_key=self.settings.anthropic_api_key
        )
        self._async_client = anthropic.AsyncAnthropic(
            api_key=self.settings.anthropic_api_key
        )

        logger.info(
            f"{self.__class__.__name__} initialized | model={self.settings.anthropic_model}"
        )

    # ─── Sync API ───────────────────────────────────────────────────────────

    def chat(self, user_message: str, reset_history: bool = False) -> str:
        """
        Gửi tin nhắn và nhận response từ Claude.
        Tự động giữ conversation history.
        """
        if reset_history:
            self.clear_history()

        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        start = time.time()
        try:
            response = self._client.messages.create(
                model=self.settings.anthropic_model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                messages=self.conversation_history,
            )
            assistant_message = response.content[0].text

            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            elapsed = round(time.time() - start, 2)
            logger.info(
                f"chat completed | tokens_in={response.usage.input_tokens} "
                f"tokens_out={response.usage.output_tokens} | {elapsed}s"
            )
            return assistant_message

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    def stream(self, user_message: str) -> Iterator[str]:
        """Streaming response — yield từng text chunk."""
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        full_response = ""
        with self._client.messages.stream(
            model=self.settings.anthropic_model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            messages=self.conversation_history,
        ) as stream:
            for text in stream.text_stream:
                full_response += text
                yield text

        self.conversation_history.append({
            "role": "assistant",
            "content": full_response
        })

    # ─── Async API ──────────────────────────────────────────────────────────

    async def achat(self, user_message: str, reset_history: bool = False) -> str:
        """Async version của chat()."""
        if reset_history:
            self.clear_history()

        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        start = time.time()
        try:
            response = await self._async_client.messages.create(
                model=self.settings.anthropic_model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                messages=self.conversation_history,
            )
            assistant_message = response.content[0].text

            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })

            elapsed = round(time.time() - start, 2)
            logger.info(
                f"achat completed | tokens_in={response.usage.input_tokens} "
                f"tokens_out={response.usage.output_tokens} | {elapsed}s"
            )
            return assistant_message

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    async def astream(self, user_message: str) -> AsyncIterator[str]:
        """Async streaming response."""
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        full_response = ""
        async with self._async_client.messages.stream(
            model=self.settings.anthropic_model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            messages=self.conversation_history,
        ) as stream:
            async for text in stream.text_stream:
                full_response += text
                yield text

        self.conversation_history.append({
            "role": "assistant",
            "content": full_response
        })

    # ─── Utilities ──────────────────────────────────────────────────────────

    def clear_history(self) -> None:
        """Xoá conversation history."""
        self.conversation_history = []
        logger.debug(f"{self.__class__.__name__} history cleared")

    def get_history(self) -> list[dict]:
        return list(self.conversation_history)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"model={self.settings.anthropic_model}, "
            f"history_len={len(self.conversation_history)})"
        )
