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
    import uvicorn

    host = "127.0.0.1"
    port = 8000
    hostname = f'{host}:{port}'

    # Check if manager already exist in jsonDB
    for agent in agents_db.get_all_records():
        hostname = agent['name']
        host, port = hostname.split(':')
        if agent['role'] == 'manager':
            break
        elif agent['role'] == 'worker':
            print(f'Found worker, and need to run: {hostname}')
            run_agent(host,port,'worker')

    else:
        # Address for hosting UI
        agents_db.get_or_create(
                Agent(
                    name=f'{host}:{port}',
                    state=State('ready'),
                    role=Role('manager'),
                    task=None
                ))
        agents_db.save()

    # Run the app on the specified host and port
    run_agent(host,port,'manager')
