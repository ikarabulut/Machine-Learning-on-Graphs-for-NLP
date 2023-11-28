from pydantic import BaseModel
from typing import List


class Article(BaseModel):
    pmid: str
    location: str
    cite: str
    abstract: str


class ArticleList(BaseModel):
    articles: List[Article] = []
