"""Punkt wejścia aplikacji FastAPI."""

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.routers import anagrams, words

app = FastAPI(
    title="Anagram REST API",
    description=(
        "Wyszukiwanie anagramów i sub-anagramów w słowniku SQLite "
        "z użyciem haszowania opartego na liczbach pierwszych."
    ),
    version="1.0.0",
)

app.include_router(anagrams.router)
app.include_router(words.router)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Zwraca 400 zamiast domyślnego 422 dla nieprawidłowego ciała żądania."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            {"detail": "Nieprawidłowe dane wejściowe.", "errors": exc.errors()}
        ),
    )


@app.get("/health", tags=["Health"], summary="Status aplikacji")
def health() -> dict:
    return {"status": "ok"}
