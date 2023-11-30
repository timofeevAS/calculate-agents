from fastapi import UploadFile
from pydantic import BaseModel
from enum import Enum

class State(str, Enum):
    """
    Model of state for worker
    """
    READY = 'ready'
    BUSY = 'busy'
    ERROR = 'error'
class Task(BaseModel):
    """
    Model of Task
    """
    name: str
    file: UploadFile


class Worker(BaseModel):
    """
    Model of Worker
    """
    task: Task
    name: str | None = None
    state: State | None = None

    def add_task(self, task: Task):
        self.task = task
        self.state = State.READY


class HeadAgent(BaseModel):
    """
    Model of HeadAgent
    """
    name: str | None = None


