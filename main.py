from jsondb import JsonDB
from models import Agent, State, Role
from utils import run_agent

# Constants
WORKERS_DB_NAME = "agents.json"
TASKS_DB_NAME = "tasks.json"

agents_db = JsonDB(WORKERS_DB_NAME)
tasks_db = JsonDB(TASKS_DB_NAME)

# This is the main entry point for the application
if __name__ == "__main__":

    # Check if manager already exist in jsonDB
    for agent in agents_db.get_all_records():
        hostname = agent['name']
        host, port = hostname.split(':')
        print(agent)
        try:
            run_agent(host,port,agent['role'])
        except Exception as e:
            print(f'Failed to run with {e}')

        print(f'Successful run: {agent}')
