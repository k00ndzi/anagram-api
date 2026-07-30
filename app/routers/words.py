"""Kontroler Word."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status

from app.db import get_connection
from app.hashing import InvalidWordError, normalize_word
from app.schemas import ErrorResponse, WordCreateRequest, WordResponse
from app.services import word_service

router = APIRouter(tags=["Word"])


def _normalize_or_400(raw: str) -> str:
    try:
        return normalize_word(raw)
    except InvalidWordError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
        ) from error


@router.post(
    "/words",
    response_model=WordResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Nieprawidłowe dane"},
        409: {"model": ErrorResponse, "description": "Słowo już istnieje"},
    },
    summary="Dodanie słowa do słownika",
)
def create_word(
    payload: WordCreateRequest,
    connection: sqlite3.Connection = Depends(get_connection),
) -> WordResponse:
    """Normalizuje słowo, wylicza jego prime hash i zapisuje je w słowniku."""
    normalized = _normalize_or_400(payload.word)

    try:
        created = word_service.add_word(connection, normalized)
    except word_service.WordAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Słowo już istnieje w słowniku: {normalized}",
        ) from error

    return WordResponse(**created)


@router.delete(
    "/words/{word}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": ErrorResponse, "description": "Nieprawidłowe dane"},
        404: {"model": ErrorResponse, "description": "Brak słowa w słowniku"},
    },
    summary="Usunięcie słowa ze słownika",
)
def remove_word(
    word: str = Path(description="Słowo do usunięcia."),
    connection: sqlite3.Connection = Depends(get_connection),
) -> Response:
    """Usuwa słowo w postaci znormalizowanej."""
    normalized = _normalize_or_400(word)

    try:
        word_service.delete_word(connection, normalized)
    except word_service.WordNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nie znaleziono słowa: {normalized}",
        ) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)
