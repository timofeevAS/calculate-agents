import sys

import uvicorn
from fastapi import FastAPI, Request, status, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from jsondb import JsonDB
from models import Worker, Task, State
from utils import find_free_port

from queue import Queue
from manager import manager_address

app = FastAPI()
# templates = Jinja2Templates(directory='templates')
from models import Task, State

from fastapi import FastAPI

app = FastAPI()


host = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
port = int(sys.argv[2]) if len(sys.argv) > 2 else 8001


@app.get("/")
def read_root():
    return {"Hello i'm worker"}

if __name__ == '__main__':
    uvicorn.run(app, host=host, port=port)