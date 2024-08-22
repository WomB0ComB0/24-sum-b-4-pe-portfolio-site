from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from enum import Enum
import time
from datetime import datetime


class SchemaType(Enum):
    PROJECTS = "projects"
    HOBBIES = "hobbies"
    TIMELINE = "timeline"
    EDUCATION = "education"
    PLACES = "places"
    WORK = "work"
    ABOUT = "about"


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
            raise ValueError("Name cannot be None")
        if type(name) != str:
            raise ValueError("Name must be a string")
        return name

    def __description(self, description: str) -> str:
        if description is None:
            raise ValueError("Description cannot be None")
        if type(description) != str:
            raise ValueError("Description must be a string")
        return description

    def __url(self, url: str) -> str:
        if url is None:
            raise ValueError("Url cannot be None")
        if type(url) != str:
            raise ValueError("Url must be a string")
        return url

    def __language(self, language: str) -> str:
        if language is None:
            raise ValueError("Language cannot be None")
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
            raise ValueError("Name cannot be None")
        if type(name) != str:
            raise ValueError("Name must be a string")
        return name

    def __description(self, description: str) -> str:
        if description is None:
            raise ValueError("Description cannot be None")
        if type(description) != str:
            raise ValueError("Description must be a string")
        return description

    def __image(self, image: str) -> str:
        if image is None:
            raise ValueError("Image cannot be None")
        if type(image) != str:
            raise ValueError("Image must be a string")
        return image


class TimelineSchema(Schema):
    def __init__(self, title: str, description: str, date: datetime) -> None:
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
            raise ValueError("Title cannot be None")
        if type(title) != str:
            raise ValueError("Title must be a string")
        return title

    def __description(self, description: str) -> str:
        if description is None:
            raise ValueError("Description cannot be None")
        if type(description) != str:
            raise ValueError("Description must be a string")
        return description

    def __date(self, date: datetime) -> datetime:
        if date is None:
            raise ValueError("Date cannot be None")
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
        description: str,
        skills: str,
        id: Optional[int] = None,  # type: ignore
    ) -> None:
        self.id = id
        self.institution = institution
        self.degree = degree
        self.startDate = startDate
        self.endDate = endDate
        self.logo = logo
        self.description = description
        self.skills = skills

    def json(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "institution": self.institution,
            "degree": self.degree,
            "startDate": self.startDate,
            "endDate": self.endDate,
            "logo": self.logo,
            "description": self.description,
            "skills": self.skills,
        }
        if self.id is not None:
            result["id"] = self.id
        return result


class PlacesSchema(Schema):
    def __init__(
        self,
        name: str,
        description: str,
        lat: float,
        lng: float,
        id: Optional[int] = None,
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.lat = lat
        self.lng = lng

    def json(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "lat": self.lat,
            "lng": self.lng,
        }
        if self.id is not None:
            result["id"] = self.id
        return result


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
        description: str,
        id: Optional[int] = None,
    ) -> None:
        self.id = id
        self.logo = logo
        self.company = company
        self.title = title
        self.type = type
        self.location = location
        self.startDate = startDate
        self.endDate = endDate
        self.description = description

    def json(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "logo": self.logo,
            "company": self.company,
            "title": self.title,
            "type": self.type,
            "location": self.location,
            "startDate": self.startDate,
            "endDate": self.endDate,
            "description": self.description,
        }
        if self.id is not None:
            result["id"] = self.id
        return result


class AboutSchema(Schema):
    def __init__(self, description: str, image: str, id: Optional[int] = None) -> None:
        self.id = id
        self.description = description
        self.image = image

    def json(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "description": self.description,
            "image": self.image,
        }
        if self.id is not None:
            result["id"] = self.id
        return result


class LandingSchema:
    """
    This class is used to create the landing page schema.
    """

    def __init__(
        self,
        education: List[Dict[str, Any]],
        places: List[Dict[str, Any]],
        work: List[Dict[str, Any]],
        about: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.education = [
            EducationSchema(
                institution=edu.get("institution", ""),
                degree=edu.get("degree", ""),
                startDate=edu.get("startDate", ""),
                endDate=edu.get("endDate", ""),
                logo=edu.get("logo", ""),
                description=edu.get("description", ""),
                skills=edu.get("skills", ""),
                id=edu.get("id"),
            )
            for edu in education
        ]
        self.places = [
            PlacesSchema(
                name=place.get("name", ""),
                description=place.get("description", ""),
                lat=place.get("lat", 0.0),
                lng=place.get("lng", 0.0),
                id=place.get("id"),
            )
            for place in places
        ]
        self.work = [
            WorkSchema(
                logo=wrk.get("logo", ""),
                company=wrk.get("company", ""),
                title=wrk.get("title", ""),
                type=wrk.get("type", ""),
                location=wrk.get("location", ""),
                startDate=wrk.get("startDate", ""),
                endDate=wrk.get("endDate", ""),
                description=wrk.get("description", ""),
                id=wrk.get("id"),
            )
            for wrk in work
        ]
        self.about = AboutSchema(
            description=about.get("description", ""),
            image=about.get("image", ""),
            id=about.get("id"),
        )
        self._set_metadata(metadata)

    def _set_metadata(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        default_metadata: Dict[str, Any] = {
            "page": 0,
            "version": "1.0.0",
            "timestamp": round(time.time()),
            "total": 1,
            "skip": 0,
            "limit": 10,
            "lastUpdated": datetime.now().isoformat(),
            "author": "Mike Odnis",
            "language": "en",
            "apiVersion": "v1",
            "dataSource": "sqlite",
            "license": "MIT",
            "contact": {
                "name": "Mike Odnis",
                "email": "mikeodnis3242004@gmail.com",
                "url": "https://mikeodnis.dev",
            },
            "tags": ["portfolio", "flask", "python"],
        }
        if metadata:
            default_metadata.update(metadata)
        self.metadata = default_metadata

    def json(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata,
            "data": {
                "education": [edu.json() for edu in self.education],
                "places": [place.json() for place in self.places],
                "work": [wrk.json() for wrk in self.work],
                "about": self.about.json(),
            },
        }
