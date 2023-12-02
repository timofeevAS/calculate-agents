import json

from pydantic import BaseModel


class JsonDB:
    """
    Class to work with JSON
    """

    def __init__(self, filename):
        # Initialize the JsonDB object
        #:param filename: The filename of the JSON file to use
        self.data = None
        self.filename = filename
        self.load()
        self.save()

    def load(self):
        """
        Load the data from the JSON file
        This method loads the data from the JSON file into the `self.data` list.
        :raises FileNotFoundError: If the file does not exist
        :raises json.JSONDecodeError: If the file is not valid JSON
        """
        try:
            with open(self.filename, 'r') as file:
                self.data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.data = []

    def save(self):
        """
        Save the data to the JSON file
        This method saves the data from the `self.data` list to the JSON file.
        :raises FileNotFoundError: If the file cannot be opened for writing
        """
        with open(self.filename, 'w') as file:
            json.dump(self.data, file, indent=4)

    def add_record(self, record: BaseModel):
        """
        Add a record to the JSON data
        This method adds the specified record to the `self.data` list.
        :param record: The record to add
        """
        self.data.append(dict(record))

    def get_record(self, index):
        """
        Get a record from the JSON data
        This method returns the record at the specified index from the `self.data` list.
        :param index: The index of the record to get
        :return: The record at the specified index, or None if the index is out of range
        """
        if 0 <= index < len(self.data):
            return self.data[index]
        else:
            return None

    def get_or_create(self, obj):
        """
        Get a record from the JSON data or create new
        Args:
            data:
        :return:
        """
        if obj not in self.data:
            self.add_record(obj)
        return obj
    def get_all_records(self):
        """
        Get all records from the JSON data
        This method returns a copy of the `self.data` list.
        :return: A list of all records
        """
        return self.data

    def remove_record(self, index):
        """
        Remove a record from the JSON data
        This method removes the record at the specified index from the `self.data` list.
        :param index: The index of the record to remove
        :raises IndexError: If the index is out of range
        """
        # Check if the index is valid
        if 0 <= index < len(self.data):
            del self.data[index]

    # change ekalugin
    def getNone(self):
        """
        Get all records where the "status" field is None

        This method returns a list of all records where the "status" field is None.

        :return: A list of records where the "status" field is None
        """
        return [worker for worker in self.data if worker.get("status") is None]

    def __contains__(self, key):
        return key in self.data
