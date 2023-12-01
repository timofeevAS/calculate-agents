import sys
import time

import uvicorn
from fastapi import FastAPI, Request, status, Response
from manager import manager_address
import datetime

from models import State, Task

app = FastAPI()
# templates = Jinja2Templates(directory='templates')
from fastapi import FastAPI

app = FastAPI()

host = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
port = int(sys.argv[2]) if len(sys.argv) > 2 else 8001

current_task = Task()
current_state = State('ready')


@app.get('/test/')
async def test():
    start = time.time()
    res = 0
    for i in range(10**8):
        res=i
    finish = time.time()
    return {"time": f"{time.time() - start} with res: {res}"}


@app.get("/")
async def read_root():
    return {f"Hello i'm worker {current_state}"}


if __name__ == '__main__':
    uvicorn.run(app, host=host, port=port)
