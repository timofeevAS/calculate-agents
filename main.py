from fastapi import FastAPI, Request
from pydantic import BaseModel
import json

app = FastAPI()


class Agent(BaseModel):
    """
    Model of Agent
    """
    task: str | None = None
    name: str | None = None
    is_busy: bool | None = None
    is_manager: bool | None = None


def save_agents_to_file(agents):
    with open('agents.json', 'w') as f:
        json.dump(agents, f)


def load_agents_from_file(filename='agents.json'):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    return data


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
    agent.is_manager = False

    agents = load_agents_from_file()  # All agents from file
    agents.append(agent.model_dump())  # Append new agent
    print(agent)
    save_agents_to_file(agents)  # Saving new agent list

    print(agent.model_dump())
    return agent


@app.get("/agents/")
async def get_agents():
    """
    Method to create agent
    :param agent:
    :param request:
    :return:
    """
    agents = load_agents_from_file()
    return agents
