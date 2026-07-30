"""Normalizacja słów i haszowanie oparte na liczbach pierwszych."""

import unicodedata
from collections import Counter

from app.config import MAX_WORD_LENGTH

LETTER_PRIMES = {
    "a": 2, "b": 3, "c": 5, "d": 7, "e": 11, "f": 13, "g": 17, "h": 19,
    "i": 23, "j": 29, "k": 31, "l": 37, "m": 41, "n": 43, "o": 47,
    "p": 53, "q": 59, "r": 61, "s": 67, "t": 71, "u": 73, "v": 79,
    "w": 83, "x": 89, "y": 97, "z": 101,
    "ó": 103, "ą": 107, "ć": 109, "ę": 113, "ł": 127, "ń": 131,
    "ś": 137, "ź": 139, "ż": 149,
}


class InvalidWordError(ValueError):
    """Słowo nie może zostać znormalizowane lub zahaszowane."""


def normalize_word(raw: str) -> str:
    """Sprowadza słowo do postaci kanonicznej używanej w bazie.

    Usuwa białe znaki, składa znaki diakrytyczne (NFC) i zamienia na małe
    litery. Zgłasza `InvalidWordError`, jeśli wynik jest pusty, za długi lub
    zawiera znak spoza `LETTER_PRIMES`.
    """
    if not isinstance(raw, str):
        raise InvalidWordError("Słowo musi być tekstem.")

    word = unicodedata.normalize("NFC", raw)
    word = "".join(word.split()).lower()

    if not word:
        raise InvalidWordError("Słowo nie może być puste.")

    if len(word) > MAX_WORD_LENGTH:
        raise InvalidWordError(
            f"Słowo jest za długie (maksymalnie {MAX_WORD_LENGTH} znaków)."
        )

    unsupported = sorted({char for char in word if char not in LETTER_PRIMES})
    if unsupported:
        raise InvalidWordError(
            "Słowo zawiera nieobsługiwane znaki: " + ", ".join(unsupported)
        )

    return word


def prime_hash(word: str) -> int:
    """Zwraca iloczyn liczb pierwszych odpowiadających literom słowa.

    Iloczyn jest niezależny od kolejności liter, więc anagramy mają identyczny
    hasz. Oczekuje słowa już znormalizowanego.
    """
    result = 1
    for char in word:
        try:
            result *= LETTER_PRIMES[char]
        except KeyError:
            raise InvalidWordError(f"Nieobsługiwany znak: {char}") from None
    return result


def letter_counts(word: str) -> Counter:
    """Zwraca licznik wystąpień poszczególnych liter."""
    return Counter(word)
