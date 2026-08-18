from pydantic import BaseModel


class CodeRepository(BaseModel):
    name: str
    url: str
    stars: int
    description: str | None = None
    primary_language: str | None = None


class ExtractedAlphaResearch(BaseModel):
    arxiv_id: str
    title: str
    published: str
    authors: list[str]
    abs_url: str
    pdf_url: str
    categories: list[str]
    summary: str
    extracted_math_concepts: list[str]
    linked_repositories: list[CodeRepository]
