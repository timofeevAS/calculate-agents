import argparse
import os
import aiohttp
import asyncio
import platform

import hashlib

import uvicorn
from fastapi import FastAPI, Request, status, Response, UploadFile, HTTPException
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
async def worker_task(request: Request):
    if whoami.role != Role('worker'):
        return JSONResponse(content={'error': 'Manager can\'t work, just control!'},
                            status_code=status.HTTP_400_BAD_REQUEST)

    data = await request.json()
    task_name = data.get("task_name", None)

    if task_name is None:
        return JSONResponse(content={"error": "task_name not provided in the request body"},
                            status_code=status.HTTP_400_BAD_REQUEST)
    file_path = os.path.join("task_sources", task_name)

    try:
        log_directory = 'tasks_log'
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        log_file_path = os.path.join(log_directory, f'{task_name}.txt')

        whoami.state = State('busy')

        # Assuming file_path contains the path to the executable
        result = subprocess.run(['python', file_path], capture_output=True, text=True)
        output = result.stdout
        error = result.stderr
        status_code = result.returncode

        with open(log_file_path, 'w') as log_file:
            log_file.write(output)

        whoami.state = State('ready')

        if status_code == 0:
            response_data = {'output': output, 'log_file_path': log_file_path}
            return JSONResponse(content=response_data, status_code=status.HTTP_200_OK)
        else:
            response_data = {'error': error, 'log_file_path': log_file_path}
            return JSONResponse(content=response_data, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return JSONResponse(content={'error': str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def give_task_to_worker(worker, task):
    payload = {'task_name': task['name']}

    async with aiohttp.ClientSession() as session:
        worker_url = f"http://{worker['name']}/workers/tasks/"
        try:
            async with session.post(worker_url, json=payload) as response:
                result = await response.json()
                print(f"Task given to worker {worker['name']}, response: {result}")
        except Exception as e:
            print(f"Error giving task to worker {worker['name']}: {str(e)}")


@app.post("/manager/tasks/")
async def append_task(file: UploadFile):
    """
    Method to append a task into queue
    :param file:
    :return:
    """

    # Prepare Task to put into queue
    task = Task(name=file.filename, file=file)
    tasks_db.add_record({'name': task.name})
    tasks_db.save()

    # Save the file to the 'task_sources' directory
    save_directory = "task_sources"
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    file_path = os.path.join(save_directory, file.filename)

    try:
        with open(file_path, "wb") as file_dest:
            file_dest.write(file.file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Try to find all free agents and give him a tasks

    free_workers = []

    for agent in agents_db.get_all_records():
        if agent['role'] == 'worker' and agent['state'] == 'ready':
            # If agent worker and free we can prepare him to task
            free_workers.append(agent)
            print(f'Worker {agent["name"]}: is ready to work! \n')

    # Giving tasks for free_workers
    tasks = tasks_db.get_all_records()
    given_tasks = 0
    print(f'All tasks: {tasks}')

    # Use asyncio.gather to perform asynchronous requests to all workers
    tasks_to_workers = []

    for index, worker in enumerate(free_workers):
        print(f"Giving task_{index} for worker {worker}")
        # Here we need give task for free agent
        tasks_to_workers.append(give_task_to_worker(worker, tasks[index]))

        given_tasks += 1
        if given_tasks == len(tasks):
            break

    await asyncio.gather(*tasks_to_workers)

    return JSONResponse(content={"message": f"{task.name} added into queue."},
                        status_code=status.HTTP_201_CREATED)


@app.get("/manager/tasks/")
async def tasks_list(request: Request):
    # Take all tasks
    tasks = tasks_db.get_all_records()

    res = [(task['name']) for task in tasks]
    print(tasks)
    return JSONResponse(content=res, status_code=status.HTTP_200_OK)


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

    uvicorn.run("agent:app", host=host, port=port, reload=False)
