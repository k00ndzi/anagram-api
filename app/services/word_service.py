"""Operacje na słowniku."""

import sqlite3

from app.hashing import prime_hash


class WordAlreadyExistsError(Exception):
    """Słowo znajduje się już w słowniku."""


class WordNotFoundError(Exception):
    """Słowa nie ma w słowniku."""


def add_word(connection: sqlite3.Connection, word: str) -> dict:
    """Zapisuje znormalizowane słowo wraz z jego haszem.

    Zgłasza `WordAlreadyExistsError`, gdy słowo już istnieje (ograniczenie
    UNIQUE na kolumnie `word`).
    """
    word_hash = str(prime_hash(word))
    try:
        cursor = connection.execute(
            "INSERT INTO dictionary (word, prime_hash) VALUES (?, ?)",
            (word, word_hash),
        )
    except sqlite3.IntegrityError as error:
        raise WordAlreadyExistsError(word) from error

    connection.commit()
    return {"id": cursor.lastrowid, "word": word, "prime_hash": word_hash}


def delete_word(connection: sqlite3.Connection, word: str) -> None:
    """Usuwa słowo ze słownika lub zgłasza `WordNotFoundError`."""
    cursor = connection.execute("DELETE FROM dictionary WHERE word = ?", (word,))
    if cursor.rowcount == 0:
        connection.rollback()
        raise WordNotFoundError(word)
    connection.commit()
