import platform

import uvicorn
from fastapi import FastAPI, Request, status, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from jsondb import JsonDB
from models import Worker, Task, State
from utils import find_free_port

from queue import Queue
import subprocess

app = FastAPI()
templates = Jinja2Templates(directory='templates')

tasks = Queue()  # Queue for storage tasks
workers = JsonDB('workers.json')  # Database in json format for storage information about workers

manager_address = ""


@app.post("/workers/append_task/")
async def append_task(task: Task):
    """
    Method to append a task into queue
    :param task:
    :return:
    """

    tasks.put(task)
    print(f"{task}")
    return Response(content={"message": f"{task} added into queue."},
                    status_code=status.HTTP_201_CREATED)


def choose_worker():
    """
    Method that returns the first busy worker
    :return:
    """
    none_workers = workers.getNone()
    if none_workers:
        return none_workers[0]
    else:
        return None


@app.post("/workers/take_task/")
async def take_task():
    """
    Method to assign a task to the first available worker
    :return:
    """
    worker_data = choose_worker()
    if worker_data:
        try:
            task = tasks.get_nowait()
            worker_data["task"] = task
            worker_data["state"] = State.READY
            workers.save()
            return {"message": f"Assigned task '{task['name']}' to worker '{worker_data['name']}'.",
                    "worker_task": worker_data["task"]}
        except Queue.Empty:
            return {"message": "Task queue is empty."}
    else:
        return {"message": "No available workers."}


@app.post("/workers/")
async def create_worker(request: Request):
    """
    Method to create worker
    :param request:
    :return:
    """

    def run_worker(host: str, port: str):
        run_server_command = ''
        if platform.system() == 'Windows':
            run_server_command = f'start python worker.py {host} {port}'
        elif platform.system() == 'Linux':
            run_server_command = f"xterm -e 'python worker.py {host} {port}'"
        else:
            print('Unsupported system')
            return False


        try:
            subprocess.run(run_server_command, shell=True)
        except subprocess.CalledProcessError as e:
            print(f"Error starting worker: {e}")

    # Filling data in a new Worker
    host = '127.0.0.1'
    port = find_free_port(8000, 8080)

    try:
        worker = Worker(name=f"{host}:{port}", state='ready')
        workers.add_record(worker.model_dump())  # Append new worker
        run_worker(host, port)  # Running new worker
    except Exception as e:
        return JSONResponse(content={'message': f'Error via creating a new worker {e}'},
                        status_code=status.HTTP_400_BAD_REQUEST)
    workers.save()  # Saving the updated worker list
    print(f'Created worker: {worker}')


    return JSONResponse(content={'message': f'Created and run a new worker {worker}'},
                        status_code=status.HTTP_201_CREATED)


@app.get("/workers/")
async def get_workers():
    """
    Method to get list of all workers
    :return
    """
    return workers.get_all_records()


@app.post("/workersIsNone/")
async def get_workers_none():
    """
    Method who return list of workers whit state is None
    :return:
    """
    return workers.getNone()


@app.get('/')
async def home_page(request: Request):
    workers_list = workers.get_all_records()
    return templates.TemplateResponse("manager.html", {"request": request, "workers": workers_list})


if __name__ == '__main__':
    host = "127.0.0.1"
    port = 8000
    manager_address = f"{host}:{port}"
    uvicorn.run("manager:app", host=host, port=port, reload=True)
