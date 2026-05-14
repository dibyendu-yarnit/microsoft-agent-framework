from collections.abc import Sequence
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel

from agent_framework import ChatResponse, ChatResponseUpdate, Content, Message, ResponseStream
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

        config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

        if stream:
            async def _stream():
                async for chunk in await self._client.aio.models.generate_content_stream(
                    model=self._model,
                    contents=user_text,
                    config=config,
                ):
                    if chunk.text:
                        yield ChatResponseUpdate(
                            contents=[Content.from_text(chunk.text)],
                            role="assistant",
                        )

            return ResponseStream(_stream(), finalizer=ChatResponse.from_updates)

        async def _call() -> ChatResponse:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=user_text,
                config=config,
            )
            return ChatResponse(messages=Message("assistant", [response.text or ""]))

        return _call()
