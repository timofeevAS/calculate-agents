from fastapi import UploadFile
from pydantic import BaseModel
from enum import Enum
from typing import Optional


class State(str, Enum):
    """
    Model of state for agent
    """
    READY = 'ready'
    BUSY = 'busy'
    ERROR = 'error'


class Role(str, Enum):
    """
    Model of role for agent
    """
    MANAGER = 'manager'
    WORKER = 'worker'

    def __str__(self):
        return self.value.capitalize()


class Task(BaseModel):
    """
    Model of Task
    """
    name: Optional[str] = None
    file: Optional[UploadFile] = None

    def __init__(self, name="", file=None):
        super().__init__(name=name, file=file)

    def __str__(self):
        return self.name


class WorkerStateUpdate(BaseModel):
    worker_name: str
    state: str
    task_name:str

class MessageInput(BaseModel):
    message: str

class Agent(BaseModel):
    """
    Model for Agent
    """
    task: Optional[Task] = None
    name: Optional[str] = None
    state: Optional[State] = None
    role: Optional[Role] = None

    def __str__(self):
        task_str = '->' + str(self.task) if self.task else ''
        return f'{self.role}: ({self.name}) -> {str(self.state)} {task_str}'
