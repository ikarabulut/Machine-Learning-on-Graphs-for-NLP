from pydantic import BaseModel


class Article(BaseModel):
    pmid: str
    location: str
    cite: str
    abstract: str
