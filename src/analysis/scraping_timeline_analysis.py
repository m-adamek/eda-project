from __future__ import annotations

from pathlib import Path
import re

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

CHANGELOG_INPUT = RAW_DIR / "scraped_product_changelogs.csv"
CONFERENCE_INPUT = RAW_DIR / "scraped_conference_sessions.csv"


PRODUCT_FEATURE_PATTERNS = {
    "pronouns": [r"\bpronouns?\b"],
    "chosen_or_preferred_names": [
        r"\bchosen names?\b",
        r"\bpreferred names?\b",
        r"\bknown as\b",
    ],
    "gender_fields": [
        r"\bgender identity\b",
        r"\bgender fields?\b",
        r"\bgender markers?\b",
        r"\bsex at birth\b",
    ],
    "display_names": [r"\bdisplay names?\b", r"\bprofile names?\b"],
    "identity_attributes": [
        r"\bidentity attributes?\b",
        r"\buser attributes?\b",
        r"\bprofile fields?\b",
        r"\bdirectory attributes?\b",
    ],
}


CONFERENCE_TOPIC_PATTERNS = {
    "identity_management": [
        r"\bidentity management\b",
        r"\bidentity and access management\b",
        r"\biam\b",
    ],
    "identity_representation": [
        r"\bidentity representation\b",
        r"\bdigital identity\b",
        r"\buser identity\b",
        r"\bprofile\b",
    ],
    "access_governance": [
        r"\baccess governance\b",
        r"\bidentity governance\b",
        r"\bprivileged access\b",
        r"\biga\b",
    ],
    "hr_technology": [
        r"\bhr technology\b",
        r"\bhr tech\b",
        r"\bhuman resources\b",
        r"\bworktech\b",
        r"\bwork tech\b",
    ],
    "ai_and_automation": [
        r"\bartificial intelligence\b",
        r"\bgen ai\b",
        r"\bagentic ai\b",
        r"\bautomation\b",
    ],
    "inclusion_and_diversity": [
        r"\binclusion\b",
        r"\binclusive\b",
        r"\bdiversity\b",
        r"\bequity\b",
        r"\bbelonging\b",
    ],
    "privacy_and_risk": [
        r"\bprivacy\b",
        r"\brisk\b",
        r"\bcompliance\b",
        r"\bsecurity\b",
        r"\bcybersecurity\b",
    ],
}


def _load_csv(path: Path, required_columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=required_columns)
    df = pd.read_csv(path)
    for column in required_columns:
        if column not in df.columns:
            df[column] = ""
    return df


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def _matched_labels(text: str, pattern_map: dict[str, list[str]]) -> list[str]:
    return [label for label, patterns in pattern_map.items() if _matches_any(text, patterns)]


def analyse_product_changelogs(path: Path = CHANGELOG_INPUT) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build product feature timeline tables from scraped changelogs."""

    df = _load_csv(
        path,
        ["product", "year", "title", "description", "url", "source", "source_url"],
    )
    if df.empty:
        empty = pd.DataFrame(columns=["year", "product", "feature", "count", "example_title", "example_url"])
        return empty, empty

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"]).copy()
    df["year"] = df["year"].astype(int)
    df["text"] = (df["title"].fillna("") + " " + df["description"].fillna("")).astype(str)
    df["detected_features"] = df["text"].apply(lambda text: _matched_labels(text, PRODUCT_FEATURE_PATTERNS))

    feature_rows = []
    for _, row in df.iterrows():
        for feature in row["detected_features"]:
            feature_rows.append(
                {
                    "year": row["year"],
                    "product": row["product"],
                    "feature": feature,
                    "title": row["title"],
                    "description": row["description"],
                    "url": row["url"],
                    "source": row["source"],
                }
            )

    feature_df = pd.DataFrame(feature_rows)
    if feature_df.empty:
        empty = pd.DataFrame(columns=["year", "product", "feature", "count", "example_title", "example_url"])
        return empty, empty

    timeline = (
        feature_df.sort_values(["year", "product", "feature"])
        .groupby(["year", "product", "feature"])
        .agg(
            count=("feature", "size"),
            example_title=("title", "first"),
            example_url=("url", "first"),
        )
        .reset_index()
    )

    first_seen = (
        feature_df.sort_values(["year", "product", "feature"])
        .groupby(["product", "feature"])
        .agg(
            first_year=("year", "min"),
            evidence_count=("feature", "size"),
            example_title=("title", "first"),
            example_url=("url", "first"),
        )
        .reset_index()
        .sort_values(["first_year", "product", "feature"])
    )
    return timeline, first_seen


def analyse_conference_sessions(path: Path = CONFERENCE_INPUT) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build conference topic trend tables from scraped session data."""

    df = _load_csv(
        path,
        ["event_name", "year", "session_title", "abstract", "url", "source", "source_url"],
    )
    if df.empty:
        empty = pd.DataFrame(columns=["year", "event_name", "topic", "sessions", "example_session", "example_url"])
        return empty, empty

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"]).copy()
    df["year"] = df["year"].astype(int)
    df["text"] = (df["session_title"].fillna("") + " " + df["abstract"].fillna("")).astype(str)
    df["detected_topics"] = df["text"].apply(lambda text: _matched_labels(text, CONFERENCE_TOPIC_PATTERNS))

    topic_rows = []
    for _, row in df.iterrows():
        for topic in row["detected_topics"]:
            topic_rows.append(
                {
                    "year": row["year"],
                    "event_name": row["event_name"],
                    "topic": topic,
                    "session_title": row["session_title"],
                    "abstract": row["abstract"],
                    "url": row["url"],
                    "source": row["source"],
                }
            )

    topic_df = pd.DataFrame(topic_rows)
    if topic_df.empty:
        empty = pd.DataFrame(columns=["year", "event_name", "topic", "sessions", "example_session", "example_url"])
        return empty, empty

    topic_year = (
        topic_df.groupby(["year", "event_name", "topic"])
        .agg(
            sessions=("topic", "size"),
            example_session=("session_title", "first"),
            example_url=("url", "first"),
        )
        .reset_index()
        .sort_values(["year", "event_name", "sessions"], ascending=[True, True, False])
    )

    dominant_topics = (
        topic_year.sort_values(["year", "event_name", "sessions"], ascending=[True, True, False])
        .drop_duplicates(subset=["year", "event_name"])
        .rename(columns={"topic": "dominant_topic"})
        .loc[:, ["year", "event_name", "dominant_topic", "sessions", "example_session", "example_url"]]
    )
    return topic_year, dominant_topics


def run_scraping_timeline_analysis() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    product_timeline, product_first_seen = analyse_product_changelogs()
    conference_topic_year, conference_dominant = analyse_conference_sessions()

    product_timeline.to_csv(PROCESSED_DIR / "product_feature_timeline.csv", index=False)
    product_first_seen.to_csv(PROCESSED_DIR / "product_feature_first_seen.csv", index=False)
    conference_topic_year.to_csv(PROCESSED_DIR / "conference_topic_year_counts.csv", index=False)
    conference_dominant.to_csv(PROCESSED_DIR / "conference_dominant_topics.csv", index=False)

    print("Scraping timeline analysis finished.")
    print(f"Product feature timeline rows: {len(product_timeline)}")
    print(f"Product first-seen rows: {len(product_first_seen)}")
    print(f"Conference topic-year rows: {len(conference_topic_year)}")
    print(f"Conference dominant-topic rows: {len(conference_dominant)}")


if __name__ == "__main__":
    run_scraping_timeline_analysis()
