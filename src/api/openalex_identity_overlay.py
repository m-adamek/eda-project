from __future__ import annotations

from pathlib import Path
import time

import pandas as pd
import requests
from tqdm import tqdm

from src.api.query_plan import OUTPUT_COLUMNS, QUERY_GROUPS



PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OPENALEX_WORKS_URL = "https://api.openalex.org/works"


## OpenAlex -> Json -> lista słowników z danymi do CSV.

def _reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    #  słowo -> lista pozycji w tekście.
    #   {"identity": [0], "matters": [1]} -->  "identity matters"

    if not inverted_index:
        return ""
    
    positions = []
    for word, indexes in inverted_index.items():
        for index in indexes:
            positions.append((index, word))
    return " ".join(word for _, word in sorted(positions))


def _extract_authorships(work: dict) -> str:
    # Wynik łączymy średnikiem, bo w CSV jedna komórka musi przechować wielu autorów.
    names = []
    for authorship in work.get("authorships", []):
        author = authorship.get("author") or {}
        if author.get("display_name"):
            names.append(author["display_name"])
    return "; ".join(names)


def _extract_topics(work: dict) -> str:
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
    params = {
        # "search" to pełnotekstowe wyszukiwanie OpenAlex.
        "search": query,
        "filter": f"publication_year:{from_year}-{to_year},type:article",
        "per-page": per_page,
        "cursor": "*",
    }
    if polite_email:
        params["mailto"] = polite_email

    records = []
    for _ in range(max_pages):
        response = requests.get(OPENALEX_WORKS_URL, params=params, timeout=30)

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

        time.sleep(0.2)

    return records


def _safe_fetch_query_group(
    group: str,
    query: str,
    *,
    max_pages_per_query: int,
    polite_email: str | None,
) -> list[dict]:
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


# pobieranko: uruchamia wszystkie zapytania z query_plan.py dla OpenAlex i zapisuje CSV.

def collect_identity_overlay_dataset(
    output_path: Path = RAW_DIR / "openalex_identity_overlay_targeted.csv",
    *,
    max_pages_per_query: int = 5,
    polite_email: str | None = None,
) -> pd.DataFrame:
    
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    total_queries = sum(len(queries) for queries in QUERY_GROUPS.values())

    with tqdm(total=total_queries, desc="OpenAlex queries") as progress:
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

    if df.empty:
        df = pd.DataFrame(columns=["openalex_id", *OUTPUT_COLUMNS])
    if not df.empty:
        # drop_duplicates usuwa duplikaty po identyfikatorze OpenAlex.
        df = df.drop_duplicates(subset=["openalex_id"]).sort_values(
            ["query_group", "year", "citations"], ascending=[True, False, False]
        )

    # zapis do csv - index=False, bo bez dodatkowej kolumny z numerem wiersza.
    df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    collect_identity_overlay_dataset()
