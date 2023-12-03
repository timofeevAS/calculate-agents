import argparse
import platform

import hashlib

import uvicorn
from fastapi import FastAPI, Request, status, Response, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse

from jsondb import JsonDB
from models import Agent, Task, State, Role
from utils import find_free_port, run_agent

import subprocess

from main import agents_db, tasks_db

app = FastAPI()
templates = Jinja2Templates(directory='templates')


def parse_args():
    parser = argparse.ArgumentParser(description='Agent Configuration')

    # Positional arguments
    parser.add_argument('host', type=str, help='Host address')

    parser.add_argument('port', type=int, help='Port number')

    # Optional argument with default value 'manager' if not provided
    parser.add_argument('--role', type=str, default='worker', choices=['manager', 'worker'],
                        help='Role of the agent (manager or worker)')

    return parser.parse_args()


args = parse_args()
whoami = Agent(name=f'{args.host}:{args.port}', role=args.role)


@app.post("/workers/tasks/")
async def append_task(file: UploadFile):
    """
    Method to append a task into queue
    :param file:
    :return:
    """

    # Prepare Task to put into queue
    task = Task(name=file.filename, file=file)
    tasks_db.add_record(task)

    print(f"Into Queue add: {task.name}")
    return JSONResponse(content={"message": f"{task.name} added into queue."},
                        status_code=status.HTTP_201_CREATED)


@app.get("/workers/tasks/")
async def tasks_queue(request: Request):
    """
    Method to append a task into queue
    :return:
    """

    response_data = []
    for task in tasks_db.get_all_records():
        response_data.append({'name': task.name})

    return JSONResponse(content=response_data,
                        status_code=status.HTTP_200_OK)


def choose_worker():
    """
    Method that returns the first busy worker
    :return:
    """
    none_workers = agents_db.getNone()
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
            task = tasks_db.get_nowait()
            worker_data["task"] = task
            worker_data["state"] = State.READY
            agents_db.save()
            return {"message": f"Assigned task '{task['name']}' to worker '{worker_data['name']}'.",
                    "worker_task": worker_data["task"]}
        except Exception as e:
            return {"message": "Task queue is empty."}
    else:
        return {"message": "No available workers."}


@app.post("/manager/workers/")
async def create_worker(request: Request):
    """
    Method to create worker
    :param request:
    :return:
    """
    if whoami.role != Role('manager'):
        return JSONResponse(content={'error': f'Not allowed. Worker can\'t making friends'},
                            status_code=status.HTTP_400_BAD_REQUEST)

    # Filling data in a new Worker
    free_port = find_free_port(8000, 8080)
    localhost = '127.0.0.1'

    worker = Agent(name=f"{localhost}:{free_port}", state=State('ready'), role=Role('worker'))
    try:
        run_agent(localhost, free_port, 'worker')  # Running new worker
    except Exception as e:
        # If we cant run new worker
        return JSONResponse(content={'message': f'Error via creating a new worker {e}'},
                            status_code=status.HTTP_400_BAD_REQUEST)
    agents_db.add_record(worker.model_dump())  # Append new worker
    agents_db.save()  # Saving the updated worker list
    print(f'Created worker: {worker}')

    return JSONResponse(content={'message': f'Created and run a new worker {worker}'},
                        status_code=status.HTTP_201_CREATED)


@app.get("/manager/workers/")
async def get_workers():
    """
    Method to get list of all workers
    :return
    """
    return agents_db.get_all_records()


@app.post("/workersIsNone/")
async def get_workers_none():
    """
    Method who return list of workers whit state is None
    :return:
    """
    return agents_db.getNone()


@app.get('/')
async def home_page(request: Request):
    name = str(whoami.role) + " " + hashlib.sha256(whoami.name.encode('utf-8')).hexdigest()[:10]

    if whoami.role == Role('manager'):
        return templates.TemplateResponse("manager.html", {"request": request, "name": name})
    else:
        return templates.TemplateResponse("worker.html", {"request": request, "name": name})


if __name__ == '__main__':
    args = parse_args()
    # Access the arguments using args.host, args.port, and args.role
    host = args.host
    port = args.port

    print(f'Initialize agent with: \n{whoami}')

    uvicorn.run("agent:app", host=host, port=port, reload=True)
