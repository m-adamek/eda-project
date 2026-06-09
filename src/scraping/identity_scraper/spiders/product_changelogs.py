from __future__ import annotations

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse
import csv
import re

import scrapy

from src.scraping.identity_scraper.items import ProductChangelogItem


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SEEDS = PROJECT_ROOT / "data" / "raw" / "product_changelog_seeds.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "scraped_product_changelogs.csv"
ANALYSIS_END_YEAR = max(2026, datetime.now().year)


FEATURE_TERMS = {
    "pronouns": ["pronoun", "pronouns"],
    "chosen_names": ["chosen name", "chosen names", "preferred name", "preferred names", "known as"],
    "gender_fields": ["gender field", "gender identity", "gender marker", "gender", "sex at birth"],
    "display_names": ["display name", "display names", "profile name"],
    "identity_attributes": ["identity attribute", "user attribute", "profile field", "directory attribute"],
}


SKIP_EXTENSIONS = {".css", ".gif", ".ico", ".jpg", ".jpeg", ".js", ".pdf", ".png", ".svg", ".webp", ".zip"}


class ProductChangelogsSpider(scrapy.Spider):
    """Crawl product changelogs and release notes.

    This spider supports the first scraping stream of the project: product
    release histories. It starts from official changelog/release-note pages,
    follows internal release-note links, and extracts entries with year and
    feature description. The downstream analysis detects when pronouns, chosen
    names or gender-related fields appear in product communication.
    """

    name = "product_changelogs"
    custom_settings = {
        "FEEDS": {
            str(OUTPUT_PATH): {
                "format": "csv",
                "overwrite": True,
                "fields": [
                    "source_type",
                    "product",
                    "source",
                    "year",
                    "date",
                    "title",
                    "description",
                    "feature_terms",
                    "url",
                    "source_url",
                    "crawl_depth",
                ],
            }
        }
    }

    def __init__(
        self,
        seeds: str | None = None,
        max_depth: str | int = 2,
        max_pages: str | int = 1500,
        only_matching: str = "false",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.seed_path = Path(seeds) if seeds else DEFAULT_SEEDS
        self.max_depth = int(max_depth)
        self.max_pages = int(max_pages)
        self.only_matching = only_matching.lower() in {"1", "true", "yes"}
        self.queued_urls: set[str] = set()
        self.visited_urls: set[str] = set()

    async def start(self):
        if not self.seed_path.exists():
            raise FileNotFoundError(
                f"Seed file not found: {self.seed_path}. "
                "Create it with columns: url,product,source,year."
            )

        with self.seed_path.open(newline="", encoding="utf-8") as seed_file:
            for row in csv.DictReader(seed_file):
                url = self._normalize_url((row.get("url") or "").strip())
                if not url:
                    continue

                self.queued_urls.add(url)
                yield scrapy.Request(
                    url,
                    callback=self.parse_release_page,
                    meta={
                        "product": (row.get("product") or self._domain_label(url)).strip(),
                        "source": (row.get("source") or self._domain_label(url)).strip(),
                        "seed_year": self._parse_year(row.get("year")),
                        "source_url": url,
                        "allowed_domain": self._domain_label(url),
                        "crawl_depth": 0,
                    },
                )

    def parse_release_page(self, response):
        current_url = self._normalize_url(response.url)
        self.visited_urls.add(current_url)

        page_title = self._first_text(
            response,
            [
                "meta[property='og:title']::attr(content)",
                "meta[name='twitter:title']::attr(content)",
                "h1::text",
                "title::text",
            ],
        )
        page_text = self._clean(" ".join(response.css("body ::text").getall()))
        page_year = (
            response.meta.get("seed_year")
            or self._extract_year(page_title)
            or self._extract_year(current_url)
            or self._extract_year(page_text)
        )

        for title, description, date_text in self._extract_entries(response, page_title, page_text):
            text = self._clean(f"{title} {description}")
            if not text:
                continue

            feature_terms = self._matched_features(text.lower())
            if self.only_matching and not feature_terms:
                continue

            year = self._extract_year(date_text) or self._extract_year(text) or page_year
            if not year:
                continue

            yield ProductChangelogItem(
                source_type="product_changelog",
                product=response.meta["product"],
                source=response.meta["source"],
                year=year,
                date=self._clean(date_text),
                title=self._clean(title),
                description=self._clean(description),
                feature_terms="; ".join(feature_terms),
                url=current_url,
                source_url=response.meta["source_url"],
                crawl_depth=response.meta["crawl_depth"],
            )

        yield from self._follow_links(response)

    def _extract_entries(self, response, page_title: str, page_text: str):
        blocks = response.css("article, main section, section, div.release, div.release-note, li, h2, h3")
        yielded = 0

        for block in blocks:
            text = self._clean(" ".join(block.css("::text").getall()))
            if len(text) < 40:
                continue

            title = self._first_text_from_block(block, ["h2::text", "h3::text", "h4::text", "strong::text"])
            date_text = self._first_text_from_block(block, ["time::attr(datetime)", "time::text"])
            if not date_text:
                date_text = self._find_date_text(text)

            if title or date_text or self._looks_like_release_text(text):
                yielded += 1
                yield title or page_title, text, date_text

        if yielded == 0 and page_text:
            yield page_title, page_text[:4000], self._find_date_text(page_text)

    def _follow_links(self, response):
        current_depth = int(response.meta.get("crawl_depth", 0))
        if current_depth >= self.max_depth or len(self.queued_urls) >= self.max_pages:
            return

        for link in response.css("a"):
            href = link.attrib.get("href", "")
            next_url = self._normalize_url(response.urljoin(href))
            link_text = self._clean(" ".join(link.css("::text").getall())).lower()
            if not self._should_follow(next_url, response.meta["allowed_domain"], link_text):
                continue

            self.queued_urls.add(next_url)
            yield scrapy.Request(
                next_url,
                callback=self.parse_release_page,
                meta={**response.meta, "crawl_depth": current_depth + 1},
            )

    @staticmethod
    def _first_text(response, selectors: list[str]) -> str:
        for selector in selectors:
            value = response.css(selector).get()
            if value:
                return value
        return ""

    @staticmethod
    def _first_text_from_block(block, selectors: list[str]) -> str:
        for selector in selectors:
            value = block.css(selector).get()
            if value:
                return value
        return ""

    @staticmethod
    def _clean(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    @staticmethod
    def _matched_features(value: str) -> list[str]:
        matches = []
        for feature, terms in FEATURE_TERMS.items():
            if any(term in value for term in terms):
                matches.append(feature)
        return matches

    @staticmethod
    def _looks_like_release_text(value: str) -> bool:
        lowered = value.lower()
        signals = ["release", "update", "new feature", "available", "rollout", "launched", "added"]
        return any(signal in lowered for signal in signals)

    @staticmethod
    def _find_date_text(value: str) -> str:
        match = re.search(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+20\d{2}\b", value, re.I)
        if match:
            return match.group(0)
        match = re.search(r"\b20[0-2]\d[-/]\d{1,2}[-/]\d{1,2}\b", value)
        return match.group(0) if match else ""

    @staticmethod
    def _extract_year(value: str) -> int | None:
        years = [int(match) for match in re.findall(r"\b(20[0-2]\d)\b", value or "")]
        return min((year for year in years if 2000 <= year <= ANALYSIS_END_YEAR), default=None)

    @classmethod
    def _parse_year(cls, value: str | None) -> int | None:
        return cls._extract_year(value or "")

    @staticmethod
    def _domain_label(url: str) -> str:
        return re.sub(r"^www\.", "", urlparse(url).netloc.lower())

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse(url.strip())
        if not parsed.scheme or not parsed.netloc:
            return url.strip()
        normalized = parsed._replace(fragment="")
        if normalized.path.endswith("/") and normalized.path != "/":
            normalized = normalized._replace(path=normalized.path.rstrip("/"))
        return urlunparse(normalized)

    def _should_follow(self, url: str, allowed_domain: str, link_text: str) -> bool:
        if not url.startswith(("http://", "https://")):
            return False
        if self._domain_label(url) != allowed_domain:
            return False
        if url in self.queued_urls or url in self.visited_urls:
            return False
        if len(self.queued_urls) >= self.max_pages:
            return False

        path = urlparse(url).path.lower()
        if any(path.endswith(extension) for extension in SKIP_EXTENSIONS):
            return False

        signal = f"{url.lower()} {link_text}"
        follow_terms = ["release", "changelog", "updates", "whats-new", "what's new", "roadmap", "history"]
        return any(term in signal for term in follow_terms) or bool(self._extract_year(signal))
