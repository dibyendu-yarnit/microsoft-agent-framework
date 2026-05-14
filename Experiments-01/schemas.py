from pydantic import BaseModel


class AgentOutput(BaseModel):
    answer: str
    sentiment: str
    score: float
