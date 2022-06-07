from dataclasses import dataclass
from datetime import datetime


@dataclass
class Source:
    id: str
    name: str


@dataclass
class Article:
    source: Source
    author: str
    title: str
    description: str
    url: str
    urlToImage: str
    datePublished: str
    content: str
