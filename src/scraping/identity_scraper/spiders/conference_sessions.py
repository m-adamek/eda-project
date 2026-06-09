from __future__ import annotations

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse
import csv
import re

import scrapy

from src.scraping.identity_scraper.items import ConferenceSessionItem


PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_SEEDS = PROJECT_ROOT / "data" / "raw" / "conference_event_seeds.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "scraped_conference_sessions.csv"
ANALYSIS_END_YEAR = max(2026, datetime.now().year)


TOPIC_TERMS = {
    "identity_management": ["identity management", "iam", "identity and access management"],
    "identity_representation": ["identity representation", "digital identity", "user identity", "profile"],
    "access_governance": ["access governance", "identity governance", "iga", "privileged access"],
    "human_resources_technology": ["hr technology", "hr tech", "human resources", "worktech", "work tech"],
    "ai_and_automation": ["artificial intelligence", " ai ", "gen ai", "agentic ai", "automation"],
    "inclusion_and_diversity": ["inclusion", "inclusive", "diversity", "equity", "belonging"],
    "privacy_and_risk": ["privacy", "risk", "compliance", "security", "cybersecurity"],
}


SKIP_EXTENSIONS = {".css", ".gif", ".ico", ".jpg", ".jpeg", ".js", ".pdf", ".png", ".svg", ".webp", ".zip"}


class ConferenceSessionsSpider(scrapy.Spider):
    """Crawl HR/IT/IAM conference and event pages for session data.

    This is the second scraping stream of the project. It collects session
    titles, abstracts and years from conference agendas or archives so the
    analysis can compare how topics changed over time, for example from
    "identity management" toward "identity representation".
    """

    name = "conference_sessions"
    custom_settings = {
        "FEEDS": {
            str(OUTPUT_PATH): {
                "format": "csv",
                "overwrite": True,
                "fields": [
                    "source_type",
                    "event_name",
                    "source",
                    "year",
                    "session_title",
                    "abstract",
                    "topic_terms",
                    "url",
                    "source_url",
                    "crawl_depth",
                ],
            }
        }
    }

    def __init__(self, seeds: str | None = None, max_depth: str | int = 2, max_pages: str | int = 2000, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seed_path = Path(seeds) if seeds else DEFAULT_SEEDS
        self.max_depth = int(max_depth)
        self.max_pages = int(max_pages)
        self.queued_urls: set[str] = set()
        self.visited_urls: set[str] = set()

    async def start(self):
        if not self.seed_path.exists():
            raise FileNotFoundError(
                f"Seed file not found: {self.seed_path}. "
                "Create it with columns: url,event_name,source,year."
            )

        with self.seed_path.open(newline="", encoding="utf-8") as seed_file:
            for row in csv.DictReader(seed_file):
                url = self._normalize_url((row.get("url") or "").strip())
                if not url:
                    continue

                self.queued_urls.add(url)
                yield scrapy.Request(
                    url,
                    callback=self.parse_event_page,
                    meta={
                        "event_name": (row.get("event_name") or self._domain_label(url)).strip(),
                        "source": (row.get("source") or self._domain_label(url)).strip(),
                        "seed_year": self._parse_year(row.get("year")),
                        "source_url": url,
                        "allowed_domain": self._domain_label(url),
                        "crawl_depth": 0,
                    },
                )

    def parse_event_page(self, response):
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

        for title, abstract in self._extract_sessions(response, page_title, page_text):
            text = self._clean(f"{title} {abstract}")
            if len(text) < 30:
                continue

            year = self._extract_year(text) or page_year
            if not year:
                continue

            yield ConferenceSessionItem(
                source_type="conference_session",
                event_name=response.meta["event_name"],
                source=response.meta["source"],
                year=year,
                session_title=self._clean(title),
                abstract=self._clean(abstract),
                topic_terms="; ".join(self._matched_topics(text.lower())),
                url=current_url,
                source_url=response.meta["source_url"],
                crawl_depth=response.meta["crawl_depth"],
            )

        yield from self._follow_links(response)

    def _extract_sessions(self, response, page_title: str, page_text: str):
        blocks = response.css(
            "article, main section, section, div.session, div.Session, div.agenda-item, "
            "li.session, li, tr"
        )
        yielded = 0

        for block in blocks:
            text = self._clean(" ".join(block.css("::text").getall()))
            if len(text) < 40:
                continue

            title = self._first_text_from_block(block, ["h2::text", "h3::text", "h4::text", "a::text", "strong::text"])
            if self._looks_like_session(text, title):
                yielded += 1
                yield title or text[:120], text

        if yielded == 0 and self._looks_like_session(page_text, page_title):
            yield page_title, page_text[:5000]

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
                callback=self.parse_event_page,
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
    def _looks_like_session(text: str, title: str) -> bool:
        lowered = f"{title} {text}".lower()
        signals = ["session", "agenda", "keynote", "workshop", "roundtable", "presentation", "speaker", "track"]
        return any(signal in lowered for signal in signals)

    @staticmethod
    def _matched_topics(value: str) -> list[str]:
        matches = []
        padded = f" {value} "
        for topic, terms in TOPIC_TERMS.items():
            if any(term in padded for term in terms):
                matches.append(topic)
        return matches

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
        follow_terms = ["session", "agenda", "program", "schedule", "presentation", "library", "archive", "event"]
        return any(term in signal for term in follow_terms) or bool(self._extract_year(signal))
