import json
import re
import os
from typing import List, Dict

class DataReader:
    def __init__(self, filename: str) -> None:
        self.filename = filename

    def read_data(self) -> List[Dict[str, str]]:
        pass

class CsvReader(DataReader):
    def read_data(self) -> List[Dict[str, str]]:
        with open(self.filename, "r", encoding="utf-8") as file:
            data = []
            for line in file:
                data.append(line.strip().split(","))
            return data

class JsonReader(DataReader):
    def read_data(self) -> List[Dict[str, str]]:
        try:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, self.filename)
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            return {"error": "File not found"}

class Processor:
    def __init__(self, data_reader: DataReader):
        self.data_reader = data_reader

    def process(self) -> List[Dict[str, str]]:
        data = self.data_reader.read_data()
        return data

class EmailValidator:
    @staticmethod
    def validate_email(email: str) -> bool:
        if re.match(
            r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email
        ):
            return True
        else:
            return False
