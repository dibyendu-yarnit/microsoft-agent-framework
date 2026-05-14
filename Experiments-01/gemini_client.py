from collections.abc import Sequence
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from agent_framework import ChatResponse, Message
import logging


logger = logging.getLogger(__name__)



class GeminiChatClient:
    additional_properties: dict = {}

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gemini-2.0-flash",
        response_schema: type[BaseModel] | None = None,
    ) -> None:
        self._model = model
        self._client = genai.Client(api_key=api_key)
        self._response_schema = response_schema

    def get_response(self, messages: Sequence[Message], *, stream: bool = False, options: Any = None, **_kwargs: Any):
        async def _call() -> ChatResponse:
            system = (options or {}).get("instructions")
            user_text = next((m.text for m in reversed(messages) if m.role == "user"), "")

            logger.debug("system   : %s", system)
            logger.debug("user_text: %s", user_text)

            config_kwargs: dict[str, Any] = {}
            if system:
                config_kwargs["system_instruction"] = system

            if self._response_schema:
                config_kwargs["response_mime_type"] = "application/json"
                config_kwargs["response_schema"] = self._response_schema

            logger.debug("config_kwargs: %s", config_kwargs)

            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=user_text,
                config=types.GenerateContentConfig(**config_kwargs) if config_kwargs else None,
            )
            return ChatResponse(messages=Message("assistant", [response.text or ""]))

        return _call()
