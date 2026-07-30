"""Wyszukiwanie anagramów i sub-anagramów."""

import sqlite3
from collections import Counter
from collections.abc import Iterator

from app.config import SQL_CHUNK_SIZE, SUBANAGRAM_COMBINATION_LIMIT
from app.hashing import letter_counts, prime_hash


def _subanagram_sort_key(word: str) -> tuple[int, str]:
    """Sub-anagramy: najpierw najdłuższe, w obrębie długości alfabetycznie."""
    return (-len(word), word)


def find_anagrams(
    connection: sqlite3.Connection, word: str, word_hash: int
) -> list[str]:
    """Zwraca słowa o identycznym haszu, pomijając samo słowo wejściowe."""
    rows = connection.execute(
        "SELECT word FROM dictionary WHERE prime_hash = ?", (str(word_hash),)
    ).fetchall()
    return sorted(row["word"] for row in rows if row["word"] != word)


def find_subanagrams(
    connection: sqlite3.Connection, word: str, word_hash: int
) -> list[str]:
    """Zwraca krótsze słowa, które można ułożyć z liter słowa wejściowego.

    Metoda bruteforce: generuje wszystkie unikalne podzbiory liter i odpytuje
    bazę po ich haszach. Dla słów, dla których liczba podzbiorów przekracza
    `SUBANAGRAM_COMBINATION_LIMIT`, przełącza się na pełny skan słownika
    z testem podzielności hasza (wariant „sprawdź każde słowo w bazie”).
    """
    counts = letter_counts(word)
    subset_hashes = _generate_subset_hashes(counts, SUBANAGRAM_COMBINATION_LIMIT)

    if subset_hashes is None:
        words = _scan_dictionary_for_divisors(connection, word_hash)
    else:
        subset_hashes.discard(1)  # pusty podzbiór
        subset_hashes.discard(word_hash)  # to są anagramy, nie sub-anagramy
        words = _select_words_by_hashes(connection, subset_hashes)

    return sorted((w for w in words if w != word), key=_subanagram_sort_key)


def _generate_subset_hashes(counts: Counter, limit: int) -> set[int] | None:
    """Generuje hasze wszystkich unikalnych podzbiorów liter słowa.

    Zwraca `None`, gdy liczba podzbiorów przekroczyłaby `limit`. Hasze buduje
    przyrostowo (iloczyn potęg liczb pierwszych), więc każdy unikalny podzbiór
    liter powstaje dokładnie raz - dwie identyczne litery nie dają duplikatów.
    """
    total = 1
    for count in counts.values():
        total *= count + 1
        if total > limit:
            return None

    hashes = {1}
    for letter, count in counts.items():
        prime = prime_hash(letter)
        powers = [prime**exponent for exponent in range(count + 1)]
        hashes = {value * power for value in hashes for power in powers}
    return hashes


def _select_words_by_hashes(
    connection: sqlite3.Connection, hashes: set[int]
) -> list[str]:
    """Pobiera słowa o podanych haszach, dzieląc zapytanie na porcje."""
    words: list[str] = []
    for chunk in _chunks(sorted(hashes), SQL_CHUNK_SIZE):
        placeholders = ",".join("?" * len(chunk))
        rows = connection.execute(
            f"SELECT word FROM dictionary WHERE prime_hash IN ({placeholders})",
            [str(value) for value in chunk],
        ).fetchall()
        words.extend(row["word"] for row in rows)
    return words


def _scan_dictionary_for_divisors(
    connection: sqlite3.Connection, word_hash: int
) -> list[str]:
    """Skanuje cały słownik i wybiera słowa, których hasz dzieli hasz wejściowy.

    Podzielność iloczynu liczb pierwszych oznacza dokładnie tyle, że litery
    danego słowa zawierają się (z krotnościami) w literach słowa wejściowego.
    """
    cursor = connection.execute("SELECT word, prime_hash FROM dictionary")
    matches: list[str] = []
    for row in cursor:
        candidate = int(row["prime_hash"])
        if candidate != word_hash and word_hash % candidate == 0:
            matches.append(row["word"])
    return matches


def _chunks(values: list[int], size: int) -> Iterator[list[int]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]
