"""Konfiguracja aplikacji (nadpisywalna przez zmienne środowiskowe)."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = Path(
    os.getenv("ANAGRAM_DB_PATH", PROJECT_ROOT / "database" / "words.db")
)

# Maksymalna długość znormalizowanego słowa przyjmowanego przez API.
MAX_WORD_LENGTH = int(os.getenv("ANAGRAM_MAX_WORD_LENGTH", "64"))

# Liczba parametrów w pojedynczym zapytaniu `WHERE prime_hash IN (...)`.
# SQLite domyślnie dopuszcza 999 zmiennych na zapytanie.
SQL_CHUNK_SIZE = 900

# Powyżej tylu unikalnych podzbiorów liter generowanie kombinacji przestaje się
# opłacać - wyszukiwanie sub-anagramów przełącza się wtedy na pełny skan bazy.
SUBANAGRAM_COMBINATION_LIMIT = int(
    os.getenv("ANAGRAM_SUBANAGRAM_COMBINATION_LIMIT", "250000")
)
