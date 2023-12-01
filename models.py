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

    def __str__(self):
        return self.name


class Worker(BaseModel):
    """
    Model of Worker
    """
    task: Task | None = None
    name: str | None = None
    state: State | None = None

    def add_task(self, task: Task):
        self.task = task
        self.state = State.READY

    def __str__(self):
        task_str = str(self.task) if self.task else ''
        return f'Worker: ({self.name}) -> {str(self.state)} -> {task_str}'
