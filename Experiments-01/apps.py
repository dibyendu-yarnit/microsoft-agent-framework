import asyncio
import logging
import os

from dotenv import load_dotenv

from agent_framework import Agent
from gemini_client import GeminiChatClient
from schemas import AgentOutput


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logging.getLogger("gemini_client").setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()


async def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY in environment")

    agent = Agent(
        name="GeminiAgent",
        client=GeminiChatClient(
            api_key=api_key,
            model=model,
            response_schema=AgentOutput,
        ),
        instructions="You are a helpful AI assistant. Provide accurate and concise answers.",
    )

    logger.info("Agent started. Type 'exit' or 'quit' to stop.")

    while True:
        user_input = input("\nYou: ").strip()

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            break

        response = await agent.run(user_input)
        output = AgentOutput.model_validate_json(response.text)

        print(f"\n  Answer    : {output.answer}")
        print(f"  Sentiment : {output.sentiment}")
        print(f"  Score     : {output.score}")


if __name__ == "__main__":
    asyncio.run(main())
