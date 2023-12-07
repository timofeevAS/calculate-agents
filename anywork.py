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
