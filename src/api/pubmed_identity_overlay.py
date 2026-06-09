from __future__ import annotations

from pathlib import Path
import time
import xml.etree.ElementTree as ET

import pandas as pd
import requests
from tqdm import tqdm

from src.api.query_plan import OUTPUT_COLUMNS, iter_queries


# Ten moduł pobiera dane z PubMed przez NCBI E-utilities.
# PubMed zwraca wyniki w dwóch krokach:
# 1. esearch: szuka identyfikatorów PMID pasujących do zapytania,
# 2. efetch: pobiera szczegółowe metadane dla znalezionych PMID.

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
NCBI_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

## PubMed -> XML -> lista słowników z danymi do CSV.

def _text(parent: ET.Element | None, path: str) -> str:
    # ElementTree pozwala szukać tagów ścieżkami, np. ".//ArticleTitle".
    # "".join(node.itertext()) zbiera tekst również z ewentualnych tagów wewnętrznych.
    if parent is None:
        return ""
    node = parent.find(path)
    return "".join(node.itertext()).strip() if node is not None else ""


def _article_year(article: ET.Element) -> int | None:
    for path in [
        ".//JournalIssue/PubDate/Year",
        ".//ArticleDate/Year",
        ".//DateCompleted/Year",
        ".//DateRevised/Year",
    ]:
        value = _text(article, path)
        if value.isdigit():
            return int(value)
    return None


def _authors(article: ET.Element) -> str:
    names = []
    for author in article.findall(".//Author"):
        last = _text(author, "LastName")
        fore = _text(author, "ForeName")
        collective = _text(author, "CollectiveName")
        name = collective or " ".join(part for part in [fore, last] if part)
        if name:
            names.append(name)
    return "; ".join(names)


def _mesh_terms(article: ET.Element) -> str:
    # MeSH to kontrolowany słownik tematów medycznych. 
    return "; ".join(
        descriptor.text or ""
        for descriptor in article.findall(".//MeshHeading/DescriptorName")
        if descriptor.text
    )


def _search_pubmed_ids(
    query: str,
    *,
    from_year: int = 2000,
    to_year: int = 2025,
    retmax: int = 100,
    api_key: str | None = None,
) -> list[str]:
    # esearch zwraca tylko listę identyfikatorów PMID.
    # Składnia (2000:2025[dp]) ogranicza datę publikacji w PubMed.
    term = f"({query}) AND ({from_year}:{to_year}[dp])"
    params = {
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retmax": retmax,
        "sort": "relevance",
    }
    if api_key:
        params["api_key"] = api_key
    response = requests.get(NCBI_ESEARCH_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("esearchresult", {}).get("idlist", [])


def _fetch_pubmed_records(ids: list[str], api_key: str | None = None) -> list[ET.Element]:
    # efetch pobiera szczegółowe rekordy XML dla listy PMID.
    if not ids:
        return []
    params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "xml",
    }
    if api_key:
        params["api_key"] = api_key
    response = requests.get(NCBI_EFETCH_URL, params=params, timeout=30)
    response.raise_for_status()
    root = ET.fromstring(response.text)
    return root.findall(".//PubmedArticle")


def fetch_query_group(
    group: str,
    query: str,
    *,
    from_year: int = 2000,
    to_year: int = 2025,
    retmax: int = 100,
    api_key: str | None = None,
) -> list[dict]:
    # Łączy dwa kroki PubMed: najpierw identyfikatory, potem pełniejsze metadane.
    ids = _search_pubmed_ids(query, from_year=from_year, to_year=to_year, retmax=retmax, api_key=api_key)
    articles = _fetch_pubmed_records(ids, api_key=api_key)
    records = []

    for article in articles:
        medline = article.find(".//MedlineCitation")
        pmid = _text(medline, "PMID")
        title = _text(article, ".//ArticleTitle")
        year = _article_year(article)
        if not title or not year:
            continue
        records.append(
            {
                "source_database": "pubmed",
                "external_id": pmid,
                "doi": _text(article, ".//ArticleId[@IdType='doi']"),
                "title": title,
                "year": year,
                "citations": 0,
                "query_group": group,
                "query": query,
                "source": _text(article, ".//Journal/Title"),
                "authors": _authors(article),
                "topics": _mesh_terms(article),
                "abstract": _text(article, ".//Abstract"),
            }
        )

    return records


def _safe_fetch_query_group(
    group: str,
    query: str,
    *,
    retmax_per_query: int,
    api_key: str | None,
) -> list[dict]:
    try:
        return fetch_query_group(group, query, retmax=retmax_per_query, api_key=api_key)
    except (requests.RequestException, ET.ParseError) as exc:
        print(f"PubMed query failed: group={group}, query={query!r}, error={exc}")
        return []


# pobieranko: uruchamia wszystkie zapytania z query_plan.py dla PubMed i zapisuje CSV.

def collect_identity_overlay_dataset(
    output_path: Path = RAW_DIR / "pubmed_identity_overlay_targeted.csv",
    *,
    retmax_per_query: int = 100,
    api_key: str | None = None,
) -> pd.DataFrame:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    queries = list(iter_queries())

    with tqdm(total=len(queries), desc="PubMed queries") as progress:
        for group, query in queries:
            records.extend(
                _safe_fetch_query_group(
                    group,
                    query,
                    retmax_per_query=retmax_per_query,
                    api_key=api_key,
                )
            )
            progress.update(1)

            time.sleep(0.34 if api_key else 0.5)

    df = pd.DataFrame(records)
    if df.empty:
        df = pd.DataFrame(columns=OUTPUT_COLUMNS)
    if not df.empty:
        df = df.drop_duplicates(subset=["external_id", "doi", "title", "year"]).sort_values(
            ["query_group", "year"], ascending=[True, False]
        )
    df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    collect_identity_overlay_dataset()
