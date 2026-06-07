from __future__ import annotations

from pathlib import Path
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from src.api.query_plan import OUTPUT_COLUMNS, iter_queries


# Ten moduł pobiera dane z Crossref.
# Crossref to baza metadanych publikacji i DOI. Używamy jej jako drugiego źródła,
# bo często zawiera inne rekordy lub inne metadane niż OpenAlex.

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CROSSREF_WORKS_URL = "https://api.crossref.org/works"


def _first(value):
    # Crossref często zwraca pola jako listy, np. title: ["Tytuł artykułu"].
    # W CSV potrzebujemy prostego tekstu, dlatego bierzemy pierwszy element listy.
    # Jeśli value nie jest listą, zwracamy je bez zmian albo pusty string.
    if isinstance(value, list) and value:
        return value[0]
    return value or ""


def _published_year(item: dict) -> int | None:
    # Crossref może podawać datę publikacji w kilku polach. Sprawdzamy je po kolei.
    # Nie używamy pola "created" jako daty publikacji, bo może oznaczać datę
    # utworzenia rekordu w Crossref, a nie datę artykułu.
    for key in ("published-print", "published-online", "published"):
        parts = item.get(key, {}).get("date-parts", [])
        if parts and parts[0]:
            return parts[0][0]
    return None


def _clean_abstract(value: str | None) -> str:
    # Abstrakt w Crossref może zawierać znaczniki HTML/XML.
    # BeautifulSoup usuwa znaczniki i zostawia czysty tekst.
    # re.sub zamienia wiele spacji/nowych linii na pojedynczą spację.
    if not value:
        return ""
    text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text)


def _authors(item: dict) -> str:
    # Autorzy w Crossref są listą słowników z polami "given" i "family".
    # Składamy je w postać "Imię Nazwisko" i łączymy średnikami.
    names = []
    for author in item.get("author", []):
        given = author.get("given", "")
        family = author.get("family", "")
        name = " ".join(part for part in [given, family] if part).strip()
        if name:
            names.append(name)
    return "; ".join(names)


def fetch_query_group(
    group: str,
    query: str,
    *,
    from_year: int = 2000,
    to_year: int = 2025,
    rows: int = 100,
    max_pages: int = 3,
    polite_email: str | None = None,
) -> list[dict]:
    # Wysyła jedno zapytanie do Crossref i zwraca listę publikacji.
    # Crossref używa parametru query.bibliographic do wyszukiwania w metadanych.
    params = {
        "query.bibliographic": query,
        # Filtr ogranicza lata i typ publikacji do artykułów czasopism.
        "filter": f"from-pub-date:{from_year},until-pub-date:{to_year},type:journal-article",
        "rows": rows,
        # Crossref także używa cursor-based pagination, czyli przewijania stron
        # wyników przez specjalny znacznik cursor.
        "cursor": "*",
        # select ogranicza odpowiedź tylko do pól, których naprawdę używamy.
        # Dzięki temu odpowiedzi są mniejsze i szybsze do przetworzenia.
        "select": "DOI,title,published-print,published-online,published,created,is-referenced-by-count,container-title,author,abstract,URL",
    }
    if polite_email:
        params["mailto"] = polite_email

    records = []
    for _ in range(max_pages):
        # requests.get pobiera jedną stronę wyników.
        response = requests.get(CROSSREF_WORKS_URL, params=params, timeout=30)
        response.raise_for_status()
        message = response.json().get("message", {})

        for item in message.get("items", []):
            title = _first(item.get("title"))
            year = _published_year(item)
            if not title or not year:
                continue
            records.append(
                {
                    "source_database": "crossref",
                    "external_id": item.get("URL", ""),
                    "doi": item.get("DOI", ""),
                    "title": title,
                    "year": year,
                    "citations": item.get("is-referenced-by-count", 0),
                    "query_group": group,
                    "query": query,
                    "source": _first(item.get("container-title")),
                    "authors": _authors(item),
                    "topics": "",
                    "abstract": _clean_abstract(item.get("abstract")),
                }
            )

        next_cursor = message.get("next-cursor")
        if not next_cursor or next_cursor == params["cursor"]:
            break
        params["cursor"] = next_cursor
        time.sleep(0.2)

    return records


def _safe_fetch_query_group(
    group: str,
    query: str,
    *,
    max_pages_per_query: int,
    polite_email: str | None,
) -> list[dict]:
    # Bezpieczna wersja pobierania: pojedynczy błąd Crossref nie przerywa całego
    # zbierania danych z innych zapytań i źródeł.
    try:
        return fetch_query_group(
            group,
            query,
            max_pages=max_pages_per_query,
            polite_email=polite_email,
        )
    except requests.RequestException as exc:
        print(f"Crossref query failed: group={group}, query={query!r}, error={exc}")
        return []


def collect_identity_overlay_dataset(
    output_path: Path = RAW_DIR / "crossref_identity_overlay_targeted.csv",
    *,
    max_pages_per_query: int = 3,
    polite_email: str | None = None,
) -> pd.DataFrame:
    # Uruchamia wszystkie zapytania z query_plan.py dla Crossref i zapisuje CSV.
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    queries = list(iter_queries())

    with tqdm(total=len(queries), desc="Crossref queries") as progress:
        for group, query in queries:
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
    if df.empty:
        df = pd.DataFrame(columns=OUTPUT_COLUMNS)
    if not df.empty:
        # Crossref może zwrócić ten sam artykuł dla kilku zapytań, więc usuwamy
        # duplikaty po DOI, tytule i roku.
        df = df.drop_duplicates(subset=["doi", "title", "year"]).sort_values(
            ["query_group", "year", "citations"], ascending=[True, False, False]
        )
    df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    collect_identity_overlay_dataset()
