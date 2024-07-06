from typing import Dict
from abc import ABC, abstractmethod
from enum import Enum

class SchemaType(Enum):
    PROJECTS = "projects"
    HOBBIES = "hobbies"

class Schema(ABC):
    @abstractmethod
    def json(self) -> Dict[str, str]:
        pass


class ProjectsSchema(Schema):
    def __init__(self, name: str, description: str, url: str, language: str):
        self.name = self.__name(name)
        self.description = self.__description(description)
        self.url = self.__url(url)
        self.language = self.__language(language)

    def json(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "language": self.language,
        }

    def __name(self, name: str) -> str:
        if name is None:
            return None
        if type(name) != str:
            raise ValueError("Name must be a string")
        return name

    def __description(self, description: str) -> str:
        if description is None:
            return None
        if type(description) != str:
            raise ValueError("Description must be a string")
        return description

    def __url(self, url: str) -> str:
        if url is None:
            return None
        if type(url) != str:
            raise ValueError("Url must be a string")
        return url

    def __language(self, language: str) -> str:
        if language is None:
            return None
        if type(language) != str:
            raise ValueError("Language must be a string")
        return language


class HobbiesSchema(Schema):
    def __init__(self, name: str, description: str, image: str):
        self.name = self.__name(name)
        self.description = self.__description(description)
        self.image = self.__image(image)

    def json(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "description": self.description,
            "image": self.image,
        }

    def __name(self, name: str) -> str:
        if name is None:
            return None
        if type(name) != str:
            raise ValueError("Name must be a string")
        return name

    def __description(self, description: str) -> str:
        if description is None:
            return None
        if type(description) != str:
            raise ValueError("Description must be a string")
        return description

    def __image(self, image: str) -> str:
        if image is None:
            return None
        if type(image) != str:
            raise ValueError("Image must be a string")
        return image
