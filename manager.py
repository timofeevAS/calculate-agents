from fastapi import FastAPI, Request
from pydantic import BaseModel
from jsondb import JsonDB
from models import Worker

app = FastAPI()

workers = JsonDB('workers.json')


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
    worker.state = False

    workers.add_record(worker.model_dump())  # Append new agent
    print(worker)
    workers.save()  # Saving new agent list

    return worker


@app.get("/workers/")
async def get_workers():
    """
    Method to get list of all workers
    """
    return workers.get_all_records()
