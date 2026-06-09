from __future__ import annotations

import argparse

from src.api.crossref_identity_overlay import collect_identity_overlay_dataset as collect_crossref
from src.api.openalex_identity_overlay import collect_identity_overlay_dataset as collect_openalex
from src.api.pubmed_identity_overlay import collect_identity_overlay_dataset as collect_pubmed


def main() -> None:
    # argparse is the standard Python library for command-line options.

    parser = argparse.ArgumentParser(description="Collect Identity Overlay literature data from multiple sources.")

    parser.add_argument("--openalex-pages", type=int, default=5)
    parser.add_argument("--crossref-pages", type=int, default=3)
    parser.add_argument("--pubmed-retmax", type=int, default=100)  #liczba artykułów

    parser.add_argument("--email", default=None, help="Optional email for polite API usage.")

    # PubMed/NCBI works without a key, but an API key allows higher request limits.
    parser.add_argument("--pubmed-api-key", default=None)

    # parse_args() reads the user's command-line options into the args object.
    args = parser.parse_args()

    # Each collector writes one CSV file into data/raw/.
    # The EDA script later loads every *identity_overlay*.csv file automatically.
    collect_openalex(max_pages_per_query=args.openalex_pages, polite_email=args.email)
    collect_crossref(max_pages_per_query=args.crossref_pages, polite_email=args.email)
    collect_pubmed(retmax_per_query=args.pubmed_retmax, api_key=args.pubmed_api_key)


if __name__ == "__main__":
    main()
