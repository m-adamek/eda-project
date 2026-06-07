from __future__ import annotations

from pathlib import Path
import time

import pandas as pd
import requests
from tqdm import tqdm

from src.api.query_plan import OUTPUT_COLUMNS, QUERY_GROUPS


# Ten moduł pobiera metadane publikacji z OpenAlex.
# OpenAlex zwraca dane jako JSON, czyli strukturę podobną do zagnieżdżonych
# słowników/list w Pythonie. Biblioteka requests wykonuje zapytanie HTTP,
# a pandas zapisuje końcową listę rekordów do CSV.

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OPENALEX_WORKS_URL = "https://api.openalex.org/works"


def _reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    # OpenAlex nie zawsze zwraca abstrakt jako zwykły tekst. Często zwraca go jako
    # "inverted index", czyli słownik: słowo -> lista pozycji w tekście.
    # Przykład uproszczony:
    #   {"identity": [0], "matters": [1]}
    # Funkcja odwraca tę strukturę z powrotem do tekstu:
    #   "identity matters"
    if not inverted_index:
        return ""
    positions = []
    for word, indexes in inverted_index.items():
        for index in indexes:
            positions.append((index, word))
    return " ".join(word for _, word in sorted(positions))


def _extract_authorships(work: dict) -> str:
    # work to pojedynczy rekord publikacji z OpenAlex.
    # get("authorships", []) pobiera listę autorów; jeśli jej nie ma, zwraca pustą
    # listę, żeby pętla się nie wywróciła.
    # Wynik łączymy średnikiem, bo w CSV jedna komórka musi przechować wielu autorów.
    names = []
    for authorship in work.get("authorships", []):
        author = authorship.get("author") or {}
        if author.get("display_name"):
            names.append(author["display_name"])
    return "; ".join(names)


def _extract_topics(work: dict) -> str:
    # OpenAlex przypisuje publikacjom tematy. Zachowujemy ich nazwy jako tekst,
    # żeby później można było ręcznie sprawdzić, czy rekord jest tematycznie trafny.
    topics = []
    for topic in work.get("topics", []):
        if topic.get("display_name"):
            topics.append(topic["display_name"])
    return "; ".join(topics)


def fetch_query_group(
    group: str,
    query: str,
    *,
    from_year: int = 2000,
    to_year: int = 2025,
    max_pages: int = 5,
    per_page: int = 200,
    polite_email: str | None = None,
) -> list[dict]:
    # Ta funkcja wykonuje jedno wyszukiwanie OpenAlex dla jednej pary:
    #   group = kategoria badawcza, np. "iam_architecture"
    #   query = konkretne zapytanie tekstowe
    #
    # Zwraca listę słowników. Każdy słownik to jedna publikacja w ujednoliconym
    # formacie, który później łatwo zapisać do CSV.
    params = {
        # "search" to pełnotekstowe wyszukiwanie OpenAlex.
        "search": query,
        # Filtr ogranicza wyniki do artykułów z zakresu lat artykułu.
        "filter": f"publication_year:{from_year}-{to_year},type:article",
        # per-page oznacza liczbę wyników na jedną stronę odpowiedzi.
        "per-page": per_page,
        # cursor="*" rozpoczyna paginację. Paginacja to pobieranie wyników
        # strona po stronie, zamiast wszystkiego naraz.
        "cursor": "*",
    }
    if polite_email:
        params["mailto"] = polite_email

    records = []
    for _ in range(max_pages):
        # requests.get wysyła zapytanie HTTP GET pod wskazany URL.
        # params=... zamienia słownik params na parametry w adresie URL.
        response = requests.get(OPENALEX_WORKS_URL, params=params, timeout=30)

        # raise_for_status() zgłasza wyjątek dla błędów HTTP, np. 429, 500.
        # Dzięki temu nie próbujemy parsować błędnej odpowiedzi jako danych.
        response.raise_for_status()

        # response.json() zamienia odpowiedź JSON na struktury Pythona.
        payload = response.json()

        for work in payload.get("results", []):
            primary_location = work.get("primary_location") or {}
            source = (primary_location.get("source") or {}).get("display_name", "")
            records.append(
                {
                    "source_database": "openalex",
                    "openalex_id": work.get("id", ""),
                    "external_id": work.get("id", ""),
                    "doi": work.get("doi", ""),
                    "title": work.get("title", ""),
                    "year": work.get("publication_year"),
                    "citations": work.get("cited_by_count", 0),
                    "query_group": group,
                    "query": query,
                    "source": source,
                    "authors": _extract_authorships(work),
                    "topics": _extract_topics(work),
                    "abstract": _reconstruct_abstract(work.get("abstract_inverted_index")),
                }
            )

        next_cursor = payload.get("meta", {}).get("next_cursor")
        if not next_cursor:
            break
        params["cursor"] = next_cursor

        # Krótka pauza zmniejsza ryzyko przeciążenia publicznego API.
        time.sleep(0.2)

    return records


def _safe_fetch_query_group(
    group: str,
    query: str,
    *,
    max_pages_per_query: int,
    polite_email: str | None,
) -> list[dict]:
    # Bezpieczna nakładka na fetch_query_group().
    # Jeśli jedno zapytanie API się nie uda, wypisujemy błąd i zwracamy pustą listę,
    # zamiast przerywać cały wieloźródłowy proces pobierania.
    try:
        return fetch_query_group(
            group,
            query,
            max_pages=max_pages_per_query,
            polite_email=polite_email,
        )
    except requests.RequestException as exc:
        print(f"OpenAlex query failed: group={group}, query={query!r}, error={exc}")
        return []


def collect_identity_overlay_dataset(
    output_path: Path = RAW_DIR / "openalex_identity_overlay_targeted.csv",
    *,
    max_pages_per_query: int = 5,
    polite_email: str | None = None,
) -> pd.DataFrame:
    # To jest funkcja wysokiego poziomu: przechodzi przez wszystkie zapytania,
    # pobiera rekordy i zapisuje gotowy CSV.
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    total_queries = sum(len(queries) for queries in QUERY_GROUPS.values())

    with tqdm(total=total_queries, desc="OpenAlex queries") as progress:
        # tqdm rysuje pasek postępu w terminalu. Nie wpływa na dane, tylko pokazuje,
        # ile zapytań już wykonano.
        for group, queries in QUERY_GROUPS.items():
            for query in queries:
                records.extend(
                    _safe_fetch_query_group(
                        group,
                        query,
                        max_pages_per_query=max_pages_per_query,
                        polite_email=polite_email,
                    )
                )
                progress.update(1)

    df = pd.DataFrame(records)
    # DataFrame to tabela pandas: coś jak arkusz kalkulacyjny w pamięci.
    # Każdy słownik z records staje się jednym wierszem.
    if df.empty:
        df = pd.DataFrame(columns=["openalex_id", *OUTPUT_COLUMNS])
    if not df.empty:
        # drop_duplicates usuwa duplikaty po identyfikatorze OpenAlex.
        # sort_values ustawia czytelny porządek: grupa, nowszy rok, więcej cytowań.
        df = df.drop_duplicates(subset=["openalex_id"]).sort_values(
            ["query_group", "year", "citations"], ascending=[True, False, False]
        )

    # to_csv zapisuje tabelę do pliku CSV.
    df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    collect_identity_overlay_dataset()
