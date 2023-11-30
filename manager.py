from fastapi import FastAPI, Request
from pydantic import BaseModel
from jsondb import JsonDB
from models import Worker, Task, State
from queue import Queue

app = FastAPI()
taskQueue = Queue() #ekalugin changes
workers = JsonDB('workers.json')

#ekalugin changes
@app.post("/workers/append_task/")
async def append_task(task: Task):
    """
    Method to append a task to the task queue
    :param task:
    :return:
    """
    taskQueue.put(task)
    print("task was put to queue")
    return {"message": "Task added to the queue."}


#ekalugin changes
def choose_worker():
    """
    Method that returns the first busy  worker
    :return:
    """
    none_workers = workers.getNone()
    if none_workers:
        return none_workers[0]
    else:
        return None

#ekalugin changes
@app.post("/workers/take_task/")
async def take_task():
    """
    Method to assign a task to the first available worker
    :return:
    """
    worker_data = choose_worker()
    if worker_data:
        try:
            task = taskQueue.get_nowait()
            worker_data["task"] = task
            worker_data["state"] = State.READY
            workers.save()
            return {"message": f"Assigned task '{task['name']}' to worker '{worker_data['name']}'.",
                    "worker_task": worker_data["task"]}
        except Queue.Empty:
            return {"message": "Task queue is empty."}
    else:
        return {"message": "No available workers."}

@app.post("/agents/")
async def create_worker(worker: Worker, request: Request):
    """
    Method to create agent
    :param worker:
    :param request:
    :return:
    """
    # Filling data in new Agent
    host, port = request.client.host, request.client.port
    worker.name = f"{host}:{port}"
    worker.state = State.BUSY

    workers.add_record(worker.model_dump())  # Append new agent
    print(worker)
    workers.save()  # Saving new agent list

    return worker


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

