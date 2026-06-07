from __future__ import annotations

from datetime import datetime
from pathlib import Path
import csv
import re

import scrapy

from src.scraping.identity_scraper.items import WebPracticeSourceItem


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SEEDS = PROJECT_ROOT / "data" / "raw" / "scrapy_seed_urls.csv"
ANALYSIS_END_YEAR = max(2025, datetime.now().year)


class WebPracticeSourcesSpider(scrapy.Spider):
    """Collect metadata-like records from manually selected web pages.

    This spider is intentionally URL-list based. It is safer for research work:
    you choose concrete pages from conference programs, vendor documentation,
    institutional repositories, reports or journal pages, and Scrapy extracts a
    normalized row for the existing EDA pipeline.
    """

    name = "web_practice_sources"

    # Scrapy sam zapisuje wynik spidera do CSV. Pola są ustawione jawnie, żeby
    # kolejność kolumn była przewidywalna i zgodna z pipeline'em EDA.
    custom_settings = {
        "FEEDS": {
            str(PROJECT_ROOT / "data" / "raw" / "scrapy_identity_overlay_targeted.csv"): {
                "format": "csv",
                "overwrite": True,
                "fields": [
                    "title",
                    "year",
                    "citations",
                    "abstract",
                    "source_database",
                    "source",
                    "url",
                    "query_group",
                    "doi",
                    "external_id",
                    "authors",
                    "topics",
                ],
            }
        }
    }

    def __init__(self, seeds: str | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Parametr `-a seeds=...` pozwala uruchomić spider na alternatywnej
        # liście URL-i, bez edytowania domyślnego pliku w data/raw/.
        self.seed_path = Path(seeds) if seeds else DEFAULT_SEEDS

    def start_requests(self):
        # Seed CSV jest ręcznie dobraną listą stron. Dzięki temu crawler jest
        # powtarzalny metodologicznie i nie eksploruje internetu samodzielnie.
        if not self.seed_path.exists():
            raise FileNotFoundError(
                f"Seed file not found: {self.seed_path}. "
                "Create it with columns: url,source,query_group,year."
            )

        with self.seed_path.open(newline="", encoding="utf-8") as seed_file:
            for row in csv.DictReader(seed_file):
                url = (row.get("url") or "").strip()
                if not url or url.startswith("#"):
                    continue

                # Dane z pliku seed trafiają do response.meta, żeby były
                # dostępne w parse_page razem z pobraną odpowiedzią HTML.
                yield scrapy.Request(
                    url,
                    callback=self.parse_page,
                    meta={
                        "source": (row.get("source") or self._domain_label(url)).strip(),
                        "query_group": (row.get("query_group") or "web_practice_sources").strip(),
                        "year": self._parse_seed_year(row.get("year")),
                    },
                )

    def parse_page(self, response):
        # Najpierw próbujemy metadanych strony, a dopiero potem nagłówków HTML.
        # Dokumentacje produktowe często mają lepsze tytuły w og:title/twitter.
        title = self._first_text(
            response,
            [
                "meta[property='og:title']::attr(content)",
                "meta[name='twitter:title']::attr(content)",
                "h1::text",
                "title::text",
            ],
        )

        # Abstract dla źródeł webowych jest przybliżeniem: zwykle bierzemy opis
        # strony albo pierwszy akapit, żeby analiza mogła szukać słów kluczowych.
        abstract = self._first_text(
            response,
            [
                "meta[name='description']::attr(content)",
                "meta[property='og:description']::attr(content)",
                "article p::text",
                "main p::text",
                "p::text",
            ],
        )

        page_text = " ".join(response.css("body ::text").getall())
        year = response.meta.get("year") or self._extract_year(page_text) or self._extract_year(response.url)

        # Webowe źródła nie mają cytowań ani DOI, więc ustawiamy wartości puste
        # lub neutralne. `source_database=web_scrapy` pozwala odróżnić je od API.
        item = WebPracticeSourceItem()
        item["title"] = self._clean(title)
        item["year"] = year or ""
        item["citations"] = 0
        item["abstract"] = self._clean(abstract)
        item["source_database"] = "web_scrapy"
        item["source"] = response.meta["source"]
        item["url"] = response.url
        item["query_group"] = response.meta["query_group"]
        item["doi"] = ""
        item["external_id"] = response.url
        item["authors"] = ""
        item["topics"] = ""
        yield item

    @staticmethod
    def _first_text(response, selectors: list[str]) -> str:
        for selector in selectors:
            value = response.css(selector).get()
            if value:
                return value
        return ""

    @staticmethod
    def _clean(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    @staticmethod
    def _extract_year(value: str) -> int | None:
        matches = re.findall(r"\b(20[0-2][0-9])\b", value or "")
        if not matches:
            return None
        years = [int(match) for match in matches]
        return min((year for year in years if 2000 <= year <= ANALYSIS_END_YEAR), default=None)

    @staticmethod
    def _parse_seed_year(value: str | None) -> int | None:
        if not value:
            return None
        try:
            year = int(value)
        except ValueError:
            return None
        return year if 2000 <= year <= ANALYSIS_END_YEAR else None

    @staticmethod
    def _domain_label(url: str) -> str:
        return re.sub(r"^www\.", "", re.sub(r"^https?://", "", url).split("/")[0])
