"""Kontroler Anagram."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.db import get_connection
from app.hashing import InvalidWordError, normalize_word, prime_hash
from app.schemas import AnagramResponse, ErrorResponse
from app.services import anagram_service

router = APIRouter(tags=["Anagram"])


@router.get(
    "/anagrams/{word}",
    response_model=AnagramResponse,
    response_model_exclude_none=True,
    responses={
        400: {"model": ErrorResponse, "description": "Nieprawidłowe słowo"},
        404: {"model": ErrorResponse, "description": "Nie znaleziono anagramów"},
    },
    summary="Wyszukiwanie anagramów",
)
def get_anagrams(
    word: str = Path(description="Słowo, dla którego szukamy anagramów."),
    subanagrams: bool = Query(
        default=False,
        description="Dołącz słowa krótsze, ułożone z liter słowa wejściowego.",
    ),
    connection: sqlite3.Connection = Depends(get_connection),
) -> AnagramResponse:
    """Zwraca anagramy słowa, opcjonalnie wraz z sub-anagramami.

    Odpowiada 404, gdy w słowniku nie ma żadnego dopasowania - przy
    `?subanagrams=true` dotyczy to obu list łącznie.
    """
    try:
        normalized = normalize_word(word)
    except InvalidWordError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error

    word_hash = prime_hash(normalized)
    found = anagram_service.find_anagrams(connection, normalized, word_hash)
    sub_found = (
        anagram_service.find_subanagrams(connection, normalized, word_hash)
        if subanagrams
        else None
    )

    if not found and not sub_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nie znaleziono anagramów dla słowa: {normalized}",
        )

    return AnagramResponse(word=normalized, anagrams=found, subanagrams=sub_found)
