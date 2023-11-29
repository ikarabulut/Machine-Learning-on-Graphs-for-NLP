from pydantic import BaseModel
from typing import List, Optional


class Article(BaseModel):
    pmid: Optional[str]
    location: Optional[str]
    cite: Optional[str]
    abstract: Optional[str]


class ArticleList(BaseModel):
    articles: List[Article] = []
