import os
import json
import sys
from abc import abstractmethod
from flask import jsonify
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Callable, Tuple, Union
from portfolio.schemas import SchemaType, ProjectsSchema, HobbiesSchema
from portfolio.constants import StatusCodeLiteral


class DataReader:
    def __init__(self, filename: str) -> None:
        self.filename = filename

    @abstractmethod
    def read_data(self) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    def write_data(self, data: List[Dict[str, str]]) -> None:
        pass


class CsvReader(DataReader):
    def read_data(self) -> List[Dict[str, str]]:
        with open(self.filename, "r", encoding="utf-8") as file:
            data = []
            for line in file:
                data.append(line.strip().split(","))
            return data

    @abstractmethod
    def write_data(self, data: List[Dict[str, str]]) -> None:
        pass


class JsonReader(DataReader):
    def read_data(self) -> Union[List[Dict[str, str]], Tuple[str, StatusCodeLiteral]]:
        try:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, self.filename)
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}).get_data(as_text=True), 404

    def write_data(
        self, data: List[Dict[str, str]]
    ) -> Union[Tuple[str, StatusCodeLiteral], None]:
        try:
            base_path = os.path.dirname(__file__)
            file_path = os.path.join(base_path, self.filename)
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(data, file)
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}).get_data(as_text=True), 404


class Processor:
    def __init__(self, data_reader: DataReader) -> None:
        self.data_reader = data_reader

    def process(self) -> Union[List[Dict[str, str]], Tuple[str, StatusCodeLiteral]]:
        data = self.data_reader.read_data()
        if data:
            return data
        raise ValueError("Data not found")


class Memoize:
    def __init__(self, func: Callable) -> None:
        self.func = func
        self.cache = {}

    def __call__(self, *args, **kwargs) -> Any:
        if args not in self.cache:
            self.cache[args] = self.func(*args, **kwargs)
        return self.cache[args]

    def memory_allocated(self) -> int:
        return sys.getsizeof(self.cache)

    def memory_allocated_in_mb(self) -> int:
        return int(self.memory_allocated() / 1024 / 1024)

    def memory_allocated_for_args(self, args: Tuple[Any, ...]) -> int:
        return sys.getsizeof(args)

    def memory_allocated_for_args_in_mb(self, args: Tuple[Any, ...]) -> int:
        return int(self.memory_allocated_for_args(args) / 1024 / 1024)

    def memory_allocated_loop(
        self, func: Callable, args: Tuple[Any, ...], iterations: int
    ) -> int:
        return sys.getsizeof(func(*args) for _ in range(iterations))

    def memory_allocated_loop_in_mb(
        self, func: Callable, args: Tuple[Any, ...], iterations: int
    ) -> int:
        return int(self.memory_allocated_loop(func, args, iterations) / 1024 / 1024)

    def clear_cache(self) -> str:
        cache_size = self.memory_allocated()
        self.cache = {}
        return f"Cleared cache. Memory allocated: {cache_size} bytes"


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
) -> Tuple[str, StatusCodeLiteral]:
    try:
        validate_request_body(body, schema_type)
        json_body[schema_type.value].append(body)
        data_reader = JsonReader(f"static/json/{schema_type.value}.json")
        data_reader.write_data(json_body[schema_type.value])
        return jsonify({"message": "Success"}).get_data(as_text=True), 200
    except ValueError as e:
        return jsonify({"error": str(e)}).get_data(as_text=True), 400
