import json

class JsonDB:
    """
    Class to work with JSON
    """
    def __init__(self, filename):
        self.data = None
        self.filename = filename
        self.load()
        self.save()

    def load(self):
        try:
            with open(self.filename, 'r') as file:
                self.data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = []

    def save(self):
        with open(self.filename, 'w') as file:
            json.dump(self.data, file, indent=4)

    def add_record(self, record):
        self.data.append(record)

    def get_record(self, index):
        if 0 <= index < len(self.data):
            return self.data[index]
        else:
            return None

    def get_all_records(self):
        return self.data

    def remove_record(self, index):
        if 0 <= index < len(self.data):
            del self.data[index]

# change ekalugin
    def getNone(self):
        return [worker for worker in self.data if worker.get("status") is None]