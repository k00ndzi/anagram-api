"""Testy API działające na tymczasowej kopii schematu bazy."""

import sqlite3
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from app import db
from app.hashing import InvalidWordError, normalize_word, prime_hash
from app.main import app

WORDS = ["kot", "kto", "tok", "ok", "to", "ko", "sen", "łza", "żaba"]


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Podstawia bazę testową w miejsce produkcyjnego słownika."""
    database_path = tmp_path / "test_words.db"
    connection = sqlite3.connect(database_path)
    connection.executescript(
        """
        CREATE TABLE dictionary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE,
            prime_hash TEXT NOT NULL
        );
        CREATE INDEX idx_prime_hash ON dictionary (prime_hash);
        """
    )
    connection.executemany(
        "INSERT INTO dictionary (word, prime_hash) VALUES (?, ?)",
        [(word, str(prime_hash(word))) for word in WORDS],
    )
    connection.commit()
    connection.close()

    @contextmanager
    def connect_test_db():
        test_connection = sqlite3.connect(database_path)
        test_connection.row_factory = sqlite3.Row
        try:
            yield test_connection
        finally:
            test_connection.close()

    monkeypatch.setattr(db, "connect", connect_test_db)
    with TestClient(app) as test_client:
        yield test_client


def test_prime_hash_is_order_independent():
    assert prime_hash("kot") == prime_hash("tok") == 31 * 47 * 71


def test_normalization_strips_whitespace_and_case():
    assert normalize_word("  KoT ") == "kot"
    assert normalize_word("ŻABA") == "żaba"


def test_normalization_rejects_unsupported_characters():
    with pytest.raises(InvalidWordError):
        normalize_word("kot1")
    with pytest.raises(InvalidWordError):
        normalize_word("   ")


def test_get_anagrams_excludes_the_word_itself(client):
    response = client.get("/anagrams/kot")
    assert response.status_code == 200
    assert response.json() == {"word": "kot", "anagrams": ["kto", "tok"]}


def test_get_anagrams_normalizes_input(client):
    response = client.get("/anagrams/%20KOT%20")
    assert response.status_code == 200
    assert response.json()["word"] == "kot"


def test_get_anagrams_with_subanagrams(client):
    response = client.get("/anagrams/kot", params={"subanagrams": "true"})
    assert response.status_code == 200
    body = response.json()
    assert body["anagrams"] == ["kto", "tok"]
    assert body["subanagrams"] == ["ko", "ok", "to"]


def test_subanagrams_absent_without_query_parameter(client):
    assert "subanagrams" not in client.get("/anagrams/kot").json()


def test_get_anagrams_returns_404_when_nothing_found(client):
    assert client.get("/anagrams/xyz").status_code == 404


def test_get_anagrams_returns_400_for_invalid_word(client):
    assert client.get("/anagrams/kot123").status_code == 400


def test_polish_letters_are_supported(client):
    assert client.post("/words", json={"word": "ABAŻ"}).status_code == 201
    response = client.get("/anagrams/żaba", params={"subanagrams": "true"})
    assert response.status_code == 200
    assert response.json() == {
        "word": "żaba",
        "anagrams": ["abaż"],
        "subanagrams": [],
    }


def test_404_when_only_the_word_itself_is_in_the_dictionary(client):
    assert client.get("/anagrams/żaba", params={"subanagrams": "true"}).status_code == 404


def test_post_word_creates_entry(client):
    response = client.post("/words", json={"word": " NoWe "})
    assert response.status_code == 201
    assert response.json()["word"] == "nowe"
    assert client.get("/anagrams/weno").json()["anagrams"] == ["nowe"]


def test_post_duplicate_word_returns_409(client):
    assert client.post("/words", json={"word": "kot"}).status_code == 409


def test_post_invalid_word_returns_400(client):
    assert client.post("/words", json={"word": "!!!"}).status_code == 400
    assert client.post("/words", json={}).status_code == 400


def test_delete_word_returns_204(client):
    assert client.delete("/words/tok").status_code == 204
    assert client.get("/anagrams/kot").json()["anagrams"] == ["kto"]


def test_delete_missing_word_returns_404(client):
    assert client.delete("/words/brak").status_code == 404


def test_subanagram_full_scan_fallback_matches_combinations(client, monkeypatch):
    """Awaryjny pełny skan bazy musi dać ten sam wynik co generowanie podzbiorów."""
    from app.services import anagram_service

    combination_result = client.get(
        "/anagrams/kot", params={"subanagrams": "true"}
    ).json()

    monkeypatch.setattr(
        anagram_service, "_generate_subset_hashes", lambda counts, limit: None
    )
    scan_result = client.get("/anagrams/kot", params={"subanagrams": "true"}).json()

    assert scan_result == combination_result
