"""Dostęp do bazy SQLite."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.config import DATABASE_PATH


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Otwiera połączenie do bazy słownika i zamyka je po użyciu."""
    if not DATABASE_PATH.exists():
        raise RuntimeError(f"Nie znaleziono bazy danych: {DATABASE_PATH}")

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def get_connection() -> Iterator[sqlite3.Connection]:
    """Zależność FastAPI: połączenie na czas obsługi pojedynczego żądania."""
    with connect() as connection:
        yield connection
