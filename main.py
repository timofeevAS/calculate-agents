from fastapi import FastAPI, Request
from pydantic import BaseModel
from jsondb import JsonDB
from models import Agent

app = FastAPI()

agents = JsonDB('agents.json')




@app.post("/agents/")
async def create_agent(agent: Agent, request: Request):
    """
    Method to create agent
    :param agent:
    :param request:
    :return:
    """
    # Filling data in new Agent
    host, port = request.client.host, request.client.port
    agent.name = f"{host}:{port}"
    agent.is_busy = False

    agents.add_record(agent.model_dump())  # Append new agent
    print(agent)
    agents.save()  # Saving new agent list

    return agent


@app.get("/agents/")
async def get_agents():
    """
    Method to get agents
    """
    return agents.get_all_records()
