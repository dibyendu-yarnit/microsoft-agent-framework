import asyncio
import os
import re

from dotenv import load_dotenv

from agent_framework import Agent
from gemini_client import GeminiChatClient
from schemas import AgentOutput

load_dotenv()


async def create_agent() -> Agent:
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY in environment")
    
    return Agent(
        name="GeminiAgent",
        client=GeminiChatClient(api_key=api_key, model=model, response_schema=AgentOutput),
        instructions="You are a helpful AI assistant. Provide accurate and concise answers.",
    )


# async def main() -> None:
#     agent = await create_agent()
#     accumulated = ""
#     last_len = 0
#     stream = agent.run("Tell me about the city of Amsterdam.", stream=True)
#     async for update in stream:
#         if update.text:
#             accumulated += update.text
#             match = re.search(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)', accumulated)
#             if match:
#                 answer = match.group(1)
#                 new_text = answer[last_len:]
#                 if new_text:
#                     print(new_text, end="", flush=True)
#                     last_len = len(answer)
#     print()
#     final = await stream.get_final_response()
#     output = AgentOutput.model_validate_json(final.text)
#     print(f"Sentiment: {output.sentiment} | Score: {output.score:.2f}")


# if __name__ == "__main__":
#     asyncio.run(main())
