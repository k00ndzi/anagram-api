"""Modele danych wejściowych i wyjściowych API."""

from pydantic import BaseModel, Field


class AnagramResponse(BaseModel):
    """Odpowiedź kontrolera anagramów.

    Pole `subanagrams` pojawia się tylko dla zapytań z `?subanagrams=true`.
    """

    word: str = Field(description="Znormalizowana postać przekazanego słowa.")
    anagrams: list[str] = Field(
        description="Słowa o identycznym haszu (bez samego słowa wejściowego)."
    )
    subanagrams: list[str] | None = Field(
        default=None,
        description="Słowa krótsze, które można ułożyć z liter słowa wejściowego.",
    )


class WordCreateRequest(BaseModel):
    """Ciało żądania `POST /words`."""

    word: str


class WordResponse(BaseModel):
    """Słowo zapisane w słowniku."""

    id: int
    word: str
    prime_hash: str


class ErrorResponse(BaseModel):
    """Ustandaryzowana odpowiedź błędu."""

    detail: str
