import os
import json
from flask import jsonify
from pydantic import BaseModel, EmailStr
from typing import List, Dict
from portfolio.schemas import SchemaType, ProjectsSchema, HobbiesSchema


class DataReader:
    def __init__(self, filename: str) -> None:
        self.filename = filename

    def read_data(self) -> List[Dict[str, str]]:
        pass

    def write_data(self, data: List[Dict[str, str]]) -> None:
        pass


class CsvReader(DataReader):
    def read_data(self) -> List[Dict[str, str]]:
        with open(self.filename, "r", encoding="utf-8") as file:
            data = []
            for line in file:
                data.append(line.strip().split(","))
            return data

    def write_data(self, data: List[Dict[str, str]]) -> None:
        pass


class JsonReader(DataReader):
    def read_data(self) -> List[Dict[str, str]]:
        try:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, self.filename)
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            return {"error": "File not found"}

    def write_data(self, data: List[Dict[str, str]]) -> None:
        try:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, self.filename)
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file)
        except FileNotFoundError:
            return {"error": "File not found"}


class Processor:
    def __init__(self, data_reader: DataReader):
        self.data_reader = data_reader

    def process(self) -> List[Dict[str, str]]:
        data = self.data_reader.read_data()
        return data


class ContactForm(BaseModel):
    name: str
    profession: str
    company: str
    email: EmailStr
    subject: str
    message: str


def validate_request_body(body: Dict[str, str], schema_type: SchemaType) -> None:
    if schema_type == SchemaType.PROJECTS:
        ProjectsSchema(**body)
    elif schema_type == SchemaType.HOBBIES:
        HobbiesSchema(**body)
    else:
        raise ValueError("Invalid schema type")


def post_function(
    body: Dict[str, str],
    json_body: Dict[str, List[Dict[str, str]]],
    schema_type: SchemaType,
) -> str:
    try:
        validate_request_body(body, schema_type)
        json_body[schema_type.value].append(body)
        data_reader = JsonReader(f"static/json/{schema_type.value}.json")
        data_reader.write_data(json_body)

    except ValueError as e:
        return jsonify({"message": str(e)}), 400
