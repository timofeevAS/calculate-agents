from pydantic import BaseModel


class Agent(BaseModel):
    """
    Model of Agent
    """
    task: str | None = None
    name: str | None = None
    is_busy: bool | None = None


class HeadAgent(BaseModel):
    """
    Model of HeadAgent
    """
    name: str | None = None