from __future__ import annotations

from pathlib import Path
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from src.api.query_plan import OUTPUT_COLUMNS, iter_queries


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CROSSREF_WORKS_URL = "https://api.crossref.org/works"


## Crossref -> Json -> lista słowników z danymi do CSV.

def _first(value):
    # np. title: ["Tytuł artykułu"].
    if isinstance(value, list) and value:     #jeśli value jest listą i nie jest pusta, zwróć pierwszy element
        return value[0]
    return value or ""


def _published_year(item: dict) -> int | None:
    # "date-parts": [[2024, 5, 12]]
    for key in ("published-print", "published-online", "published"): 
        parts = item.get(key, {}).get("date-parts", [])
        if parts and parts[0]:     #jeśli parts i pierwszy element parts istnieją, zwróć pierwszy element pierwszego elementu parts (rok)
            return parts[0][0]
    return None                    #jeśli nie można znaleźć daty publikacji, zwróć None


def _clean_abstract(value: str | None) -> str:
    # BeautifulSoup usuwa znaczniki HTML/XML
    # re.sub zamienia wiele spacji/nowych linii na pojedynczą spację.
    if not value:
        return ""
    text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text)


def _authors(item: dict) -> str:
    names = []
    for author in item.get("author", []):
        given = author.get("given", "")
        family = author.get("family", "")
        name = " ".join(part for part in [given, family] if part).strip()
        if name:
            names.append(name)
    return "; ".join(names)


def fetch_query_group(
    group: str,                  #nazwa grupy zapytań, np. 'AI' 
    query: str,                  #zapytanie tekstowe, np. 'artificial intelligence'
    *,                           #po * wszystkie kolejne argumenty muszą być przekazane jako argumenty nazwane.
    from_year: int = 2000,
    to_year: int = 2025,
    rows: int = 100,
    max_pages: int = 3,
    polite_email: str | None = None,
) -> list[dict]:
    params = {
        "query.bibliographic": query,
        "filter": f"from-pub-date:{from_year},until-pub-date:{to_year},type:journal-article",
        "rows": rows,
        "cursor": "*",
        "select": "DOI,title,published-print,published-online,published,created,is-referenced-by-count,container-title,author,abstract,URL",
    }
    if polite_email:
        params["mailto"] = polite_email

    records = []
    for _ in range(max_pages):
        # requests.get pobiera jedną stronę wyników.
        response = requests.get(CROSSREF_WORKS_URL, params=params, timeout=30)
        response.raise_for_status()                             #jeśli odpowiedź ma status błędu HTTP, podnosi wyjątek, który jest obsługiwany w _safe_fetch_query_group.
        message = response.json().get("message", {})            #parsuje json, zamienia jsona na strukture pythona - tu słownik 

        for item in message.get("items", []):
            title = _first(item.get("title"))
            year = _published_year(item)
            if not title or not year:
                continue   #pomijamy jak nie ma tytułu lub roku, bo to dane kluczowe do analizy
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



# pobieranko: uruchamia wszystkie zapytania z query_plan.py dla Crossref i zapisuje CSV. 

def collect_identity_overlay_dataset(
    output_path: Path = RAW_DIR / "crossref_identity_overlay_targeted.csv",
    *, 
    max_pages_per_query: int = 3,
    polite_email: str | None = None,
) -> pd.DataFrame:

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
