# Anagram REST API

REST API do wyszukiwania **anagramów** i **sub-anagramów** w słowniku języka polskiego
liczącym ponad 3,2 miliona słów. Sercem projektu jest haszowanie oparte na liczbach
pierwszych (*Prime Number Hashing*), dzięki któremu wyszukiwanie anagramów sprowadza
się do jednego zapytania po indeksie - niezależnie od rozmiaru słownika.

```console
$ curl "http://127.0.0.1:8000/anagrams/kot?subanagrams=true"
{
  "word": "kot",
  "anagrams": ["kto", "tok"],
  "subanagrams": ["ko", "ok", "ot", "to"]
}
```

## Metodologia

### Haszowanie liczbami pierwszymi

Każdej literze przypisana jest unikalna liczba pierwsza, a hasz słowa to **iloczyn**
liczb pierwszych jego liter:

```
kot  →  k(31) · o(47) · t(71)  =  103 447
tok  →  t(71) · o(47) · k(31)  =  103 447
```

Pełne mapowanie (26 liter łacińskich + 9 polskich) znajduje się w
[`app/hashing.py`](app/hashing.py):

```python
LETTER_PRIMES = {
    "a": 2, "b": 3, "c": 5, "d": 7, "e": 11, "f": 13, "g": 17, "h": 19,
    "i": 23, "j": 29, "k": 31, "l": 37, "m": 41, "n": 43, "o": 47,
    "p": 53, "q": 59, "r": 61, "s": 67, "t": 71, "u": 73, "v": 79,
    "w": 83, "x": 89, "y": 97, "z": 101,
    "ó": 103, "ą": 107, "ć": 109, "ę": 113, "ł": 127, "ń": 131,
    "ś": 137, "ź": 139, "ż": 149,
}
```

### Normalizacja

Przed wyliczeniem hasza i przed **każdym** zapytaniem do bazy słowo przechodzi tę samą
ścieżkę: normalizacja → usunięcie białych znaków → zamiana na małe litery.
Dzięki temu `"  KoT "`, `"KOT"` i `"kot"` trafiają w ten sam rekord, a zapis i odczyt
są symetryczne.

### Sub-anagramy

Sub-anagram to słowo krótsze, które można ułożyć z liter słowa wejściowego. W języku
liczb pierwszych oznacza to dokładnie tyle, że **hasz sub-anagramu dzieli hasz słowa**.

## Baza danych

Słowa pochodzą ze słownika **[sjp.pl](https://sjp.pl/sl/growy/)** (słownik growy).
Gotowa baza SQLite jest do pobrania pod adresem:

**<https://www.dropbox.com/scl/fi/h2adb153ws6uqbkxs0cz8/words.db?rlkey=30gc3y7zwmv552t71sv80970q&st=bz0qdb0w&dl=0>**

Pobrany plik należy umieścić w katalogu `database/` pod nazwą `words.db`
(albo wskazać własną ścieżkę zmienną `ANAGRAM_DB_PATH`):

**Tabela `dictionary`** - 3 240 240 rekordów:

| Kolumna | Typ | Opis |
| --- | --- | --- |
| `id` | INTEGER | klucz główny |
| `word` | TEXT | słowo w postaci znormalizowanej, `UNIQUE` |
| `prime_hash` | TEXT | iloczyn liczb pierwszych; `TEXT`, aby uniknąć *integer overflow* |

Indeks `idx_prime_hash` na kolumnie `prime_hash` zapewnia szybkie wyszukiwanie
pełnych anagramów.

## Uruchomienie

**Wymagania:** Python 3.11 lub nowszy. Nic poza tym - baza to plik SQLite, nie ma
serwera bazodanowego do konfigurowania.

Poniższe komendy zapisane są w wersji dla Windows. Na Linuksie
i macOS wszystko działa tak samo, zmienia się tylko ścieżka do interpretera
w środowisku wirtualnym: zamiast `.venv\Scripts\python.exe` wpisz `.venv/bin/python`.

### Krok 1 - wejdź do katalogu projektu

```bash
cd anagram-api
```

### Krok 2 - utwórz środowisko wirtualne

```bash
python -m venv .venv
```

W katalogu projektu pojawi się folder `.venv` z odizolowaną instalacją Pythona.
Krok wykonuje się tylko raz.

### Krok 3 - zainstaluj zależności

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Instaluje FastAPI, Uvicorn, Pydantic oraz pytest (do testów).

### Krok 4 - przygotuj bazę danych

Jeśli w katalogu `database/` nie ma pliku `words.db`, pobierz go i umieść w wskazanym katalogu.

### Krok 5 - uruchom serwer

```bash
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Dokumentacja API

### `GET /anagrams/{word}`

Wyszukuje anagramy słowa. Oblicza *prime hash* przekazanego słowa i zwraca wszystkie
słowa ze słownika o identycznym haszu.

**Parametr ścieżki**

| Nazwa | Typ | Opis |
| --- | --- | --- |
| `word` | string | Słowo do przeszukania (normalizowane po stronie API). |

**Parametr zapytania**

| Nazwa | Typ | Domyślnie | Opis |
| --- | --- | --- | --- |
| `subanagrams` | boolean | `false` | Dołącza listę krótszych słów, które można ułożyć z liter słowa wejściowego. |

**Przykład - zapytanie standardowe**

```bash
curl "http://127.0.0.1:8000/anagrams/listen"
```

```json
{
  "word": "listen",
  "anagrams": ["listne", "stleni"]
}
```

**Przykład - z sub-anagramami**

```bash
curl "http://127.0.0.1:8000/anagrams/maszyna?subanagrams=true"
```

```json
{
  "word": "maszyna",
  "anagrams": ["szamany"],
  "subanagrams": [
    "maszyn", "mazany", "namazy", "naszym", "sazany", "szaman",
    "amany", "asany", "azyma", "azyna", "..."
  ]
}
```

> Lista `subanagrams` dla słowa `maszyna` zawiera 70 pozycji - powyżej pokazano
> jej początek. Sub-anagramy sortowane są od najdłuższych.

**Kody odpowiedzi**

| Kod | Kiedy |
| --- | --- |
| `200 OK` | znaleziono dopasowania |
| `400 Bad Request` | słowo puste, za długie lub zawiera znak spoza mapowania |
| `404 Not Found` | brak anagramów (przy `?subanagrams=true` - brak jakichkolwiek dopasowań) |

```json
{ "detail": "Nie znaleziono anagramów dla słowa: qqqqqq" }
```

---

### `POST /words`

Dodaje pojedyncze słowo do słownika. Słowo jest normalizowane, a jego *prime hash*
wyliczany po stronie API.

**Ciało żądania**

```json
{ "word": "zgróblański" }
```

```bash
curl -X POST http://127.0.0.1:8000/words \
     -H "Content-Type: application/json" \
     -d '{"word": "zgróblański"}'
```

**Odpowiedź - `201 Created`**

```json
{
  "id": 3240241,
  "word": "zgróblański",
  "prime_hash": "14987388237352242"
}
```

**Kody odpowiedzi**

| Kod | Kiedy |
| --- | --- |
| `201 Created` | słowo zapisane |
| `400 Bad Request` | brak pola `word`, słowo puste lub z niedozwolonym znakiem |
| `409 Conflict` | słowo już istnieje w słowniku (ograniczenie `UNIQUE`) |

---

### `DELETE /words/{word}`

Usuwa słowo ze słownika. Porównanie odbywa się na postaci znormalizowanej, więc
`DELETE /words/ZGRÓBLAŃSKI` usunie rekord `zgróblański`.

```bash
curl -X DELETE http://127.0.0.1:8000/words/zgróblański
```

**Kody odpowiedzi**

| Kod | Kiedy |
| --- | --- |
| `204 No Content` | słowo usunięte |
| `400 Bad Request` | słowo w nieprawidłowej postaci |
| `404 Not Found` | słowa nie było w bazie |

---

## Testy i weryfikacja

```bash
.venv\Scripts\python.exe -m pytest -q
```

Powinno wypisać `17 passed`. Testy działają na własnej, tymczasowej bazie i nie
modyfikują słownika.
