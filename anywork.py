import asyncio
import json

import aiohttp
import requests
from fastapi.responses import JSONResponse
from fastapi import status, FastAPI
from jsondb import JsonDB
from agent import args, give_task_to_worker
from models import Agent
from main import agents_db, tasks_db

app = FastAPI()


# async def send_request():
#     while True:
#         free_workers = []
#         for agent in agents_db.get_all_records():
#             if agent['role'] == 'worker' and agent['state'] == 'ready':
#                 free_workers.append(agent)
#
#         if free_workers:
#             tasks = tasks_db.get_all_records()
#             tasks_args = []
#
#             for index, workers in enumerate(free_workers):
#                 if index >= len(tasks):
#                     break
#                 print(f"Giving task_{index} for worker {workers}")
#                 tasks_args.append((workers, tasks[index]))
#             print(tasks_args)
#             await asyncio.gather(*(give_task_to_worker(*args) for args in tasks_args))
#         await asyncio.sleep(30)
#
# @app.post("/manager/ping")
# async def check_free_workers_and_ping():
#     asyncio.create_task(check_free_workers_and_ping())
#     return JSONResponse(content={"message": "Check for free workers scheduled."},
#                         status_code=status.HTTP_200_OK)

jsonData = JsonDB


def get_manager_address():
    with open('agents.json', 'r') as file:
        agent_data = json.load(file)
        for agent in agent_data:
            if agent.role == 'manager':
                return agent.name
async def check_and_assign_task(manager_adress):
    payload = {'message': 'any work'}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"http://{manager_adress}/manager/tasks/", json=payload) as response:
                result = await response.json()
                print(f"give answer from manager {manager_adress}, response: {result}")
        except Exception as e:
            print(f"Error contacting the manager {manager_adress}: {str(e)}")
def timer():
    tick = 0
    while True:
        if tick % 30000 == 0:
            manger_name = get_manager_address()
            check_and_assign_task(manger_name)
        else:
            tick = tick + 1
