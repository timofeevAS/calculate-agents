import time
import requests
from main import agents_db


def get_manager_address():
    for agent in agents_db.get_all_records():
        if agent['role'] == 'manager':
            return agent['name']

    return -1


def check_and_assign_task(manager_address):
    payload = {'message': 'any work'}
    url = f'http://{manager_address}/manager/message/'

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx and 5xx)

        # Check if the response is successful (status code 2xx)
        if 200 <= response.status_code < 300:
            print(response.json())  # Access the response content as needed
            return True
        else:
            # Handle unexpected status codes (if needed)
            print(f"Unexpected status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        # Handle exceptions (e.g., connection error)
        print(f"Request failed: {e}")
        return False

def timer(manager_address):
    start_time = time.time()
    while True:
        if (time.time() - start_time) >= 5:
            print('5 second... go!')
            if not check_and_assign_task(manager_address):
                manager_address = get_manager_address()
            start_time = time.time()


if __name__ == '__main__':
    manager_address = get_manager_address()

    if not manager_address:
        print('No manager')
        exit(0)
    else:
        print(f'Starting efficiency checker to control -> {manager_address}')
    timer(manager_address)
