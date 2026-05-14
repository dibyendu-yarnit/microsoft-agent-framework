from agent_framework import Agent
from agent_framework_gemini import GeminiChatClient
from dotenv import load_dotenv
import asyncio
import os

# Load environment variables from .env file
load_dotenv()

# Initialize the GeminiChatClient with API key and model from environment variables
client = GeminiChatClient(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model=os.getenv("GOOGLE_MODEL")
)

# Create an instance of the Agent with the GeminiChatClient and instructions
agent = Agent(
    name="GeminiAgent",
    client=client,
    instructions="You are a helpful AI assistant. Provide accurate and concise answers.",
    default_options={"tool_choice": None},
)


# Define an asynchronous main function to run the agent and print the response
async def main():
    response = await agent.run("What is the capital of France?")
    print(response)


# Run the main function using asyncio
asyncio.run(main())