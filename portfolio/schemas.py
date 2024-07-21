from typing import Dict, Any, List
from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime


class SchemaType(Enum):
    PROJECTS = "projects"
    HOBBIES = "hobbies"
    TIMELINE = "timeline"


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


class TimelineSchema(Schema):
    def __init__(self, title: str, description: str, date: datetime):
        self.title = self.__title(title)
        self.description = self.__description(description)
        self.date = self.__date(date)

    def json(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "description": self.description,
            "date": self.date.strftime("%Y-%m-%d"),
        }

    def __title(self, title: str) -> str:
        if title is None:
            return None
        if type(title) != str:
            raise ValueError("Title must be a string")
        return title

    def __description(self, description: str) -> str:
        if description is None:
            return None
        if type(description) != str:
            raise ValueError("Description must be a string")
        return description

    def __date(self, date: datetime) -> datetime:
        if date is None:
            return None
        if type(date) != datetime:
            raise ValueError("Date must be a datetime")
        return date


class EducationSchema(Schema):
    def __init__(
        self,
        institution: str,
        degree: str,
        startDate: str,
        endDate: str,
        logo: str,
        description: List[str],
        skills: List[str],
    ):
        self.institution = institution
        self.degree = degree
        self.startDate = startDate
        self.endDate = endDate
        self.logo = logo
        self.description = description
        self.skills = skills

    def json(self) -> Dict[str, Any]:
        return {
            "institution": self.institution,
            "degree": self.degree,
            "startDate": self.startDate,
            "endDate": self.endDate,
            "logo": self.logo,
            "description": self.description,
            "skills": self.skills,
        }


class PlacesSchema(Schema):
    def __init__(self, name: str, description: str, lat: float, lng: float):
        self.name = name
        self.description = description
        self.lat = lat
        self.lng = lng

    def json(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "lat": self.lat,
            "lng": self.lng,
        }


class WorkSchema(Schema):
    def __init__(
        self,
        logo: str,
        company: str,
        title: str,
        type: str,
        location: str,
        startDate: str,
        endDate: str,
        description: List[str],
    ):
        self.logo = logo
        self.company = company
        self.title = title
        self.type = type
        self.location = location
        self.startDate = startDate
        self.endDate = endDate
        self.description = description

    def json(self) -> Dict[str, Any]:
        return {
            "logo": self.logo,
            "company": self.company,
            "title": self.title,
            "type": self.type,
            "location": self.location,
            "startDate": self.startDate,
            "endDate": self.endDate,
            "description": self.description,
        }


class AboutSchema(Schema):
    def __init__(self, description: str, image: str):
        self.description = description
        self.image = image

    def json(self) -> Dict[str, str]:
        return {
            "description": self.description,
            "image": self.image,
        }
