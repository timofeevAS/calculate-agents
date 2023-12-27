import argparse
import os
import time

import aiohttp
import asyncio
import platform
import requests

import hashlib

import uvicorn
from fastapi import FastAPI, Request, status, UploadFile, HTTPException, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, FileResponse
from starlette.staticfiles import StaticFiles

from jsondb import JsonDB
from models import *
from utils import find_free_port, run_agent, hash_str

import subprocess

import logging
from logging.handlers import RotatingFileHandler

from main import agents_db, tasks_db

app = FastAPI()
templates = Jinja2Templates(directory='templates')
origins = [
    "http://localhost"
]

app.mount("/static", StaticFiles(directory="templates/static"), name="static")

# setting up logging
# Create a formatter for log messages
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

# Create a rotating file handler to log messages to a file 'app.log'
# - Rotate files when they reach 100000 bytes
# - Keep up to 3 backup log files
log_handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=3)
log_handler.setFormatter(log_formatter)

# Get the root logger and configure it
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

# --- Parsing command-line arguments ---
def parse_args():
    """Parses command-line arguments for agent configuration."""

   # Positional arguments (required):
    parser = argparse.ArgumentParser(description='Agent Configuration')

    # Positional arguments
    parser.add_argument('host', type=str, help='Host address')

    parser.add_argument('port', type=int, help='Port number')

    parser.add_argument('manager_address', type=str, help='Manager address')

    # Optional argument with default value 'manager' if not provided
    parser.add_argument('--role', type=str, default='worker', choices=['manager', 'worker'],
                        help='Role of the agent (manager or worker)')

    return parser.parse_args()

#--- Configuration and initialization ---
args = parse_args()
whoami = Agent(name=f'{args.host}:{args.port}', role=args.role)
manager_address = args.manager_address

# --- Endpoint for handling worker tasks ---
@app.post("/workers/tasks/")
async def worker_task(request: Request):
    """Handles incoming tasks assigned to this worker."""
    # --- Function to update worker state ---
    def update_worker_state(worker_name, new_state, task_name):
        """Notifies the manager about a change in the worker's state."""
        endpoint = f'http://{manager_address}/manager/worker_state/'
        payload = {'worker_name': worker_name, 'state': new_state, 'task_name': task_name}
        response = requests.patch(endpoint, json=payload)

        if response.status_code == 200:
            print(f"Worker state updated to {new_state}")
        else:
            print(f"Failed to update worker state. Status code: {response.status_code}")

    if whoami.role != Role('worker'):
        logger.error('The manager cannot perform tasks, only control!')
        return JSONResponse(content={'error': 'Manager can\'t work, just control!'},
                            status_code=status.HTTP_400_BAD_REQUEST)

    # Get data about task
    data = await request.json()
    task_name = data.get("task_name", None)

    if task_name is None:
        logger.error('The task name was not provided in the request body.')
        return JSONResponse(content={"error": "task_name not provided in the request body"},
                            status_code=status.HTTP_400_BAD_REQUEST)
    file_path = os.path.join("task_sources", task_name)

    update_worker_state(whoami.name, 'busy', task_name)
    whoami.state = State('busy')

    try:
        log_directory = 'tasks_log'
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        log_file_path = os.path.join(log_directory, f'{task_name}_{hash_str(whoami.name)}.txt')

        # Assuming file_path contains the path to the executable
        result = subprocess.run(['python', file_path], capture_output=True, text=True)
        output = result.stdout
        error = result.stderr
        status_code = result.returncode

        print(f'Result of processing: {result}')

        with open(log_file_path, 'w') as log_file:
            log_file.write(output)

        if status_code == 0:
            response_data = {'output': output, 'log_file_path': log_file_path}
            logger.info(f'The task was completed successfully: {response_data}')
            return JSONResponse(content=response_data, status_code=status.HTTP_200_OK)
        else:
            response_data = {'error': error, 'log_file_path': log_file_path}
            logger.error(f'Task execution error: {response_data}')
            return JSONResponse(content=response_data, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.exception(f'An exception has occurred: {str(e)}')
        return JSONResponse(content={'error': str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        whoami.state = State('ready')
        update_worker_state(whoami.name, 'ready', task_name)


async def give_task_to_worker(worker: dict, task: dict):
    """
    Function for assigning a task to a specified worker.

    This function first removes the task from the database and then sends it to the specified worker.

    Args:
        worker (dict): Dictionary containing the worker's name and address.
        task (dict): Dictionary containing the task's name and other relevant information.

    Returns:
        None
    """

    # Prepare the payload for the HTTP request
    payload = {'task_name': task['name']}

    # Open an asynchronous HTTP session
    async with aiohttp.ClientSession() as session:
        # Construct the URL for sending the task to the worker
        worker_url = f"http://{worker['name']}/workers/tasks/"
        try:
            # Remove the task from the database
            # (Assuming a tasks_db object is available)
            index = tasks_db.get_index({"name": task['name']})
            print(f'try to find {task["name"]} with index {index}')
            tasks_db.remove_record(index)
            tasks_db.save()

            # Send the task to the specified worker
            async with session.post(worker_url, json=payload) as response:
                # Retrieve the response from the worker
                result = await response.json()

                # Log the task delivery status
                logger.info(f"Task given to worker {worker['name']}, response: {result}")
                print(f"Task given to worker {worker['name']}, response: {result}")

        # Handle any exceptions that may occur during task assignment
        except Exception as e:
            logger.exception(f"Error giving task to worker {worker['name']}: {str(e)}")
            print(f"Error giving task to worker {worker['name']}: {str(e)}")


@app.post("/manager/tasks/")
async def append_task(file: UploadFile):
    """
    Method to append a task into queue
    :param file:
    :return:
    """

    # Prepare Task to put into queue
    task_name = f'{file.filename.split(".")[0]}_{hash_str(str(time.time()))}.{file.filename.split(".")[1]}'
    task = Task(name=task_name, file=file)
    tasks_db.add_record({'name': task.name})
    tasks_db.save()
    logger.info("The task was prepare to put into queue")

    # Save the file to the 'task_sources' directory
    save_directory = "task_sources"
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    file_path = os.path.join(save_directory, task.name)

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
            logger.info(f'Worker {agent["name"]}: is ready to work!')

    # Giving tasks for free_workers
    tasks = tasks_db.get_all_records()
    logger.info(f'All tasks: {tasks}')

    # Use asyncio.gather to perform asynchronous requests to all workers
    task_args = []

    for index, worker in enumerate(free_workers):
        if index >= len(tasks):
            break  # Break if there are no more tasks
        print(f"Giving task_{index} for worker {worker}")
        logger.info(f"Giving task_{index} for worker {worker}")
        task_args.append((worker, tasks[index]))

    print(task_args)

    # await asyncio.gather(*(give_task_to_worker(*args) for args in task_args))

    tasks = [asyncio.create_task(give_task_to_worker(*args)) for args in task_args]

    return JSONResponse(content={"message": f"{task.name} added into queue."},
                        status_code=status.HTTP_201_CREATED)


@app.get("/manager/tasks/")
async def tasks_list(request: Request):
    """Provides a list of all available tasks."""
    # Try to fetch all tasks from the database using `tasks_db`
    try:
        # Take all tasks
        tasks = tasks_db.get_all_records()

        # Format the task list as a list of task names
        res = [(task['name']) for task in tasks]
        logger.info("The task list has been successfully received")

        # Return the task list as JSON response with status code 200 (OK)
        return JSONResponse(content=res, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.exception(f'Error when getting the task list: {str(e)}')

        # Handle any errors during task retrieval
        return JSONResponse(content={'error': str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.post("/manager/workers/")
async def create_worker(request: Request):
    """
    Method to create worker
    :param request:
    :return:
    """

    try:
        # Verify that the current agent is the manager
        if whoami.role != Role('manager'):
            logger.error('Unacceptable. The manager cannot create workers.')
            return JSONResponse(content={'error': f'Not allowed. Worker can\'t making friends'},
                                status_code=status.HTTP_400_BAD_REQUEST)

        # Get a free port for the new worker
        # Filling data in a new Worker
        free_port = find_free_port(8000, 8080)

        # Set up the worker's name and address
        localhost = '127.0.0.1'

        # Create a new `Agent` object for the worker
        worker = Agent(name=f"{localhost}:{free_port}", state=State('ready'), role=Role('worker'))

        # Attempt to launch the worker process
        try:
            run_agent(localhost, free_port, 'worker', manager_address=manager_address)  # Running new worker
        except Exception as e:
            # If launching the worker fails, handle the error
            logger.error(f'Error when creating a new worker: {e}')
            return JSONResponse(content={'message': f'Error via creating a new worker {e}'},
                                status_code=status.HTTP_400_BAD_REQUEST)

        # Add the newly created worker to the agents database
        agents_db.get_or_create(worker.model_dump())  # Append new worker
        agents_db.save()  # Saving the updated worker list
        logger.info(f'A new worker has been created and launched: {worker}')

        # Return a success message with the worker's name
        return JSONResponse(content={'message': f'Created and run a new worker {worker}'},
                            status_code=status.HTTP_201_CREATED)
    except Exception as e:
        logger.exception(f'An exception has occurred: {str(e)}')
        return JSONResponse(content={'error': str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/manager/workers/")
async def get_workers():
    """
    Method to get list of all workers
    :return
    """
    try:
        # Method to get list of all workers
        workers = agents_db.get_all_records()
        logger.info("The list of all workers has been successfully received")
        return workers
    except Exception as e:
        logger.exception(f'Error when getting a list of all workers: {str(e)}')
        return JSONResponse(content={'error': str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.patch('/manager/worker_state/')
async def set_worker_state(request: Request, update_data: WorkerStateUpdate):
    worker = None
    for agent in agents_db.get_all_records():
        if agent['name'] == update_data.worker_name:
            worker = agent
            agent['state'] = update_data.state
            if update_data.state != 'ready':
                agent['task'] = update_data.task_name
            else:
                agent['task'] = ''
            agents_db.save()
            break

    # If worker ready, and we have tasks we need to give one more for him
    tasks = list(tasks_db.get_all_records())
    if update_data.state == 'ready' and len(tasks):
        print(f'Worker {worker} is free try give a task!')
        task_to_complete = None
        for task in tasks_db.get_all_records():
            correct = True
            for agent in agents_db.get_all_records():
                if agent['task'] == task['name']:
                    correct = False
                    break
            if correct:
                task_to_complete = task
                break

        print(f'Try to give task ({task_to_complete}) for {update_data.worker_name}')
        asyncio.create_task(
            give_task_to_worker(
                worker,
                task_to_complete
            )
        )
        return JSONResponse(content={'message': f'Worker: {worker["name"]}  go processing: {tasks[0]}'},
                            status_code=status.HTTP_200_OK)

    # If agent can continue working
    if len(tasks_db.get_all_records()) and update_data.state == 'ready':
        print('Still working bro')
        return JSONResponse(content={'message': f'Worker {worker}: go still working '},
                            status_code=status.HTTP_200_OK)

    return JSONResponse(content={'message': f'Worker: {worker["name"]}  changed state to: {update_data.state}'},
                        status_code=status.HTTP_200_OK)


async def give_task():
    """Checks for available tasks and distributes them to ready workers."""
    # Identify free workers
    free_workers = []

    for agent in agents_db.get_all_records():
        if agent['role'] == 'worker' and agent['state'] == 'ready':
            # If agent worker and free we can prepare him to task 
            #(if worker is free, add it to the list of available workers)
            free_workers.append(agent)
            logger.info(f'Worker {agent["name"]}: is ready to work!')

    # Giving tasks for free_workers
    tasks = tasks_db.get_all_records()

    # Check if there are enough tasks for all available workers
    print(f'Checking queue for tasks and free agents: {len(free_workers)} workers for {len(tasks)} tasks')
    logger.info(f'All tasks: {tasks}')

    # Use asyncio.gather to perform asynchronous requests to all workers
    task_args = []

    # Distribute tasks to available workers
    for index, worker in enumerate(free_workers):
        if index >= len(tasks):
            break  # Break if there are no more tasks
        print(f"Giving task_{index} for worker {worker}")
        logger.info(f"Giving task_{index} for worker {worker}")

        # Create task arguments for each worker and task
        task_args.append((worker, tasks[index]))

    # Execute task distribution asynchronously using `asyncio.create_task()'
    tasks = [asyncio.create_task(give_task_to_worker(*args)) for args in task_args]

    return len(task_args)


@app.post('/manager/message/')
async def check_any_works(request: Request, input: MessageInput):
    """
    This function reading message, incoming to manager

    but now function NOT using, cause we have feedback when Worker can do one more task
    """
    try:
        if input.message == 'any work':
            num = give_task()
        return JSONResponse(content={'message': f'Running {await num} tasks'}, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.exception(f'The problem with retransmitting the task: {str(e)}')
        return JSONResponse(content={'error': str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def check_tasks(background_tasks: BackgroundTasks):
    """
    Feedback configure, NOT USED
    """
    print('Starting inf loop (daemon)')
    while True:
        await give_task()
        await asyncio.sleep(5)


@app.get("/download/{file_name}")
async def download_file(file_name: str):
    log_directory = 'tasks_log'
    file_path = os.path.join(log_directory, file_name)

    return FileResponse(file_path, media_type="application/octet-stream", filename=file_name)


@app.get('/manager/results/')
async def get_results():
    log_directory = 'tasks_log'
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    files = os.listdir(log_directory)

    results = []

    for file_name in files:
        file_path = os.path.join(log_directory, file_name)
        results.append({'file_name': file_name, 'path': file_path})

    return JSONResponse(content=results, status_code=status.HTTP_200_OK)


@app.get('/results')
async def results_page(request: Request):
    if whoami.role != Role('manager'):
        return HTTPException(status_code=404)

    return templates.TemplateResponse('results.html', {"request": request, "name": whoami.name})


@app.get('/')
async def home_page(request: Request, background_tasks: BackgroundTasks):
    try:
        # Generate a unique name using role and a hashed version of the agent's name
        name = str(whoami.role) + " " + hashlib.sha256(whoami.name.encode('utf-8')).hexdigest()[:10]

        if whoami.role == Role('manager'):
            # If the agent is a manager, render the manager.html template
            # If role manager try to give_tasks

            logger.info("Rendering manager.html for the manager.")
            return templates.TemplateResponse("manager.html", {"request": request, "name": name})
        else:
            # If the agent is not a manager, render the worker.html template
            logger.info("Rendering worker.html for the worker.")
            return templates.TemplateResponse("worker.html", {"request": request, "name": name})
    except Exception as e:
        # Log any exceptions that may occur
        logger.exception(f'Error while rendering home page: {str(e)}')
        return JSONResponse(content={'error': str(e)}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


async def check_connection():
    async def become_manager():
        pass

    async def attempt_heal():
        run_agent(manager_address.split(':')[0], manager_address.split(':')[1], 'manager', manager_address)

    async def is_manager_alive(manager_url: str):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(manager_url) as response:
                    if response.status == 200:
                        print("Manager is alive.")
                    else:
                        print(f"Error: Manager returned status code {response.status}")
            except Exception as e:
                print(f"Error: Unable to connect to the manager. {e}")
                await attempt_heal()

    while True:
        print(f"Checking connection with Manager: '{manager_address}'")
        await is_manager_alive(f'http://{manager_address}')
        await asyncio.sleep(30)  # 30 seconds awaiting


@app.on_event("startup")
async def startup_event():
    if whoami.role == Role('worker'):
        asyncio.create_task(check_connection())


if __name__ == '__main__':
    """"Launchs a server using UVicorn library and given 'host' and 'port';
        Logs init info and/or exception
    """
    args = parse_args()
    host = args.host
    port = args.port

    logger.info(f'Initialization agent: \n{whoami} with manager_address: {manager_address} ')
    print(f'Init {whoami}')
    try:
        uvicorn.run("agent:app", host=host, port=port, reload=False)
    except Exception as e:
        logger.exception(f'Во время запуска сервера UVicorn произошло исключение: {str(e)}')
