from pydantic import BaseModel


class Worker(BaseModel):
    """
    Model of Worker
    """
    task: str | None = None
    name: str | None = None
    state: bool | None = None


class HeadAgent(BaseModel):
    """
    Model of HeadAgent
    """
    name: str | None = None