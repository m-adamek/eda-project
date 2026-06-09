# Exploratory analysis for the Identity Overlay article

This project supports an exploratory literature analysis for the article draft:

**Projektowanie systemów informatycznych wspierających inkluzywność: reprezentacja tożsamości użytkownika**

The analysis narrows the previous broad workplace-inclusion project toward the article's core research problem: how user identity is represented, propagated and contextualised in organisational information systems, especially when legal identity differs from social/display identity.

## Research focus

The exploratory analysis is designed to support the article sections on methodology, literature gap and current state of identity representation in organisational systems. It maps publication metadata from OpenAlex, Crossref and PubMed around:

- identity representation, digital identity, preferred names and pronouns,
- transgender workplace experience, misgendering, deadnaming and outing,
- HR systems, organisational systems and workplace technologies,
- Identity and Access Management, provisioning, federation and attributes,
- inclusive design, Value Sensitive Design and human/user-centred design,
- relational/legal status and same-sex marriage as examples of rigid data models,
- AI bias and digital risks in organisational systems.

## Data

Current legacy raw dataset:

`data/raw/openalex_workplace_inclusion.csv`

It contains OpenAlex records collected for workplace inclusion queries from 2000-2025. The current file has three fields:

- `title`
- `year`
- `citations`

Because the legacy raw dataset only contains titles, the analysis should be treated as an exploratory mapping of publication signals, not as a systematic review or full bibliometric study.

For datasets closer to the article draft, collect targeted exports:

```powershell
.\.venv\Scripts\python.exe -m src.api.openalex_identity_overlay
.\.venv\Scripts\python.exe -m src.api.crossref_identity_overlay
.\.venv\Scripts\python.exe -m src.api.pubmed_identity_overlay
```

Or collect all sources in one run:

```powershell
.\.venv\Scripts\python.exe -m src.api.collect_all_sources --email your-email@example.com
```

These commands create:

`data/raw/openalex_identity_overlay_targeted.csv`
`data/raw/crossref_identity_overlay_targeted.csv`
`data/raw/pubmed_identity_overlay_targeted.csv`

The Scrapy part of the project now has two research streams.

First, product changelog scraping collects release notes from products such as
Microsoft 365, Google Workspace, Slack and Workday. It is designed to answer:
when did product communication start mentioning pronouns, preferred/chosen
names, display names or gender-related fields?

```powershell
.\.venv\Scripts\scrapy.exe crawl product_changelogs
.\.venv\Scripts\scrapy.exe crawl product_changelogs -a max_depth=3 -a max_pages=3000
```

Second, conference/event scraping collects session titles and abstracts from
IAM, cybersecurity and HR technology events such as Gartner IAM Summit,
Identiverse, RSAC and HR Technology Conference. It is designed to answer: how
does conference language change over time, for example from identity management
toward identity representation?

```powershell
.\.venv\Scripts\scrapy.exe crawl conference_sessions
.\.venv\Scripts\scrapy.exe crawl conference_sessions -a max_depth=3 -a max_pages=4000
```

Scrapy writes:

`data/raw/scraped_product_changelogs.csv`
`data/raw/scraped_conference_sessions.csv`

Then analyse scraped timelines:

```powershell
.\.venv\Scripts\python.exe -m src.analysis.scraping_timeline_analysis
```

This creates:

`data/processed/product_feature_timeline.csv`
`data/processed/product_feature_first_seen.csv`
`data/processed/conference_topic_year_counts.csv`
`data/processed/conference_dominant_topics.csv`

The scraping rationale is documented in `docs/SCRAPING_ZAMYSL.md`.

The targeted API exports use shared query groups for identity representation, transgender workplace experience, IAM architecture, inclusive design and relational/legal status. If any `*identity_overlay*.csv` files exist in `data/raw/`, `main.py` merges and deduplicates them automatically; otherwise it falls back to the legacy workplace-inclusion CSV.

## Run

```powershell
.\.venv\Scripts\python.exe main.py
```

The command generates processed CSV files in `data/processed/` and charts in `visuals/`.

## Outputs

- `data/processed/identity_overlay_enriched.csv` - raw records enriched with article-specific topic flags.
- `data/processed/source_summary.csv` - publication counts by source database.
- `data/processed/topic_summary.csv` - publication counts, citation totals and time range per topic.
- `data/processed/topic_year_counts.csv` - yearly publication counts per topic.
- `data/processed/topic_cooccurrence.csv` - topic co-occurrence matrix based on title matches.
- `data/processed/top_relevant_articles.csv` - highly relevant and cited records for manual screening.
- `data/processed/product_feature_timeline.csv` - yearly product changelog evidence for identity-related features.
- `data/processed/product_feature_first_seen.csv` - first detected year for each product/feature pair.
- `data/processed/conference_topic_year_counts.csv` - yearly conference-session counts by topic.
- `data/processed/conference_dominant_topics.csv` - dominant topic per event/year.
- `visuals/01_publication_trend.png` - overall trend of publications.
- `visuals/02_topic_trends.png` - trends for the article's main topic groups.
- `visuals/03_topic_cooccurrence.png` - heatmap of topic co-occurrences.

## Suggested interpretation in the article

Use the generated outputs as exploratory evidence for the literature gap:

1. There is a visible publication field around workplace inclusion and organisational diversity.
2. A smaller subset explicitly connects identity representation with organisational or HR systems.
3. IAM and system-architecture language appears separately from transgender workplace experience and inclusive design language.
4. This separation supports the article's claim that the technical representation of identity is under-integrated with social research on identity, safety and inclusion.

A Polish methodology note drafted for the article is available in `docs/METODOLOGIA_EDA.md`.

Additional project documentation:

- `docs/README_PLIKI.md` - what each file and folder does.
- `docs/FUNKCJE_METODY_KOMENDY.md` - short catalogue of functions, methods and commands grouped by library/tool.
- `docs/SCRAPING_ZAMYSL.md` - current scraping design: product changelogs and conference/event sessions.
- `docs/OPIS_PROJEKTU_I_FIGUR.md` - Polish description of the project and generated figures.

## Project structure

```text
data/raw/       Source exports from OpenAlex, Crossref and PubMed
data/processed/ Generated exploratory-analysis tables
docs/           Project notes and file/function documentation
notebooks/      Original OpenAlex collection notebook
src/analysis/   Reusable EDA code
src/scraping/   Scrapy collectors for selected non-API web sources
visuals/        Generated charts
```
