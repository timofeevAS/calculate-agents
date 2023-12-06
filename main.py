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

    manager_ran = False
    manager_address = None
    # Try to find manager in agents db
    for agent in agents_db.get_all_records():
        if agent['role'] == 'manager':
            manager_address = agent['name']
            break

    # TODO IF WE DIDN'T FIND MANAGER NEED TO CREATE!!!!!!!


    # Execute agents from DataBase
    for agent in agents_db.get_all_records():
        hostname = agent['name']
        host, port = hostname.split(':')
        print(agent)
        try:
            run_agent(host, port, agent['role'], manager_address=manager_address)
            manager_ran = (manager_ran or agent['role'] == 'manager')
        except Exception as e:
            print(f'Failed to run with {e}')
        print(f'Successful run: {agent} with address of manager: {manager_address}')

    if not manager_ran:
        manager = Agent(
            name='127.0.0.1:8000',
            role=Role('manager'),
            state=State('ready'),
            task=None
        )

        agents_db.add_record(manager)
        agents_db.save()
        run_agent('127.0.0.1', '8000', 'manager', '')
