# Opis plików projektu

Ten plik jest szybką mapą repozytorium: co znajduje się w danym miejscu i po co
jest potrzebne.

## Katalog główny

- `README.md` - główny opis projektu, źródeł danych, sposobu uruchamiania i wyników.
- `main.py` - najprostszy punkt startowy; uruchamia analizę EDA z `src/analysis/identity_overlay_eda.py`.
- `pyproject.toml` - deklaracja projektu i zależności w nowoczesnym formacie Pythona.
- `requirements.txt` - lista zależności do instalacji przez `pip`.
- `uv.lock` - plik blokady zależności dla narzędzia `uv`.
- `scrapy.cfg` - konfiguracja startowa Scrapy, wskazuje ustawienia w `src/scraping/identity_scraper/settings.py`.
- `.python-version` - preferowana wersja Pythona dla projektu.
- `.gitignore` - lista plików i katalogów pomijanych przez Git, np. `.venv` i `__pycache__`.

## `docs/`

- `README_PLIKI.md` - ten plik; opis roli plików i katalogów.
- `FUNKCJE_METODY_KOMENDY.md` - katalog funkcji, metod i komend używanych w projekcie, pogrupowany według bibliotek.
- `METODOLOGIA_EDA.md` - notatka metodologiczna po polsku do wykorzystania w artykule.
- `OPIS_PROJEKTU_I_FIGUR.md` - opis projektu i wygenerowanych figur.
- `TEMATY_BADAWCZE.txt` - wcześniejsza lista tematów i kierunków badawczych.

## `src/api/`

- `query_plan.py` - wspólna strategia zapytań i schemat kolumn dla kolektorów API.
- `openalex_identity_overlay.py` - pobiera metadane publikacji z OpenAlex.
- `crossref_identity_overlay.py` - pobiera metadane publikacji z Crossref.
- `pubmed_identity_overlay.py` - pobiera metadane publikacji z PubMed/NCBI.
- `collect_all_sources.py` - uruchamia kolektory OpenAlex, Crossref i PubMed w jednej komendzie.
- `__init__.py` - oznacza katalog jako pakiet Pythona.

## `src/analysis/`

- `identity_overlay_eda.py` - główna logika analizy: ładowanie danych, deduplikacja, flagi tematyczne, tabele wynikowe i wykresy.
- `__init__.py` - oznacza katalog jako pakiet Pythona.

## `src/scraping/`

- `identity_scraper/items.py` - definicja rekordu Scrapy zapisywanego do CSV.
- `identity_scraper/settings.py` - ustawienia Scrapy: robots.txt, tempo pobierania, kodowanie eksportu.
- `identity_scraper/spiders/web_practice_sources.py` - spider pobierający metadane z ręcznie dobranych stron webowych.
- `__init__.py` - pliki pakietowe Pythona.

## `data/raw/`

- `openalex_workplace_inclusion.csv` - starszy zbiór bazowy z OpenAlex.
- `openalex_identity_overlay_targeted.csv` - docelowy eksport z OpenAlex.
- `crossref_identity_overlay_targeted.csv` - docelowy eksport z Crossref.
- `pubmed_identity_overlay_targeted.csv` - docelowy eksport z PubMed.
- `scrapy_seed_urls.csv` - ręcznie dobrana lista stron dla Scrapy.
- `scrapy_seed_sources.md` - uzasadnienie doboru źródeł webowych.
- `scrapy_identity_overlay_targeted.csv` - plik wynikowy Scrapy, jeśli spider został uruchomiony.

## `data/processed/`

- `identity_overlay_enriched.csv` - główny wynik analizy z flagami tematycznymi.
- `source_summary.csv` - liczba rekordów według źródła danych.
- `topic_summary.csv` - podsumowanie kategorii tematycznych.
- `topic_year_counts.csv` - liczba publikacji według roku i tematu.
- `topic_cooccurrence.csv` - macierz współwystępowania tematów.
- `top_relevant_articles.csv` - rekordy najbardziej warte ręcznego przejrzenia.

## `visuals/`

- `01_publication_trend.png` - trend liczby publikacji.
- `02_topic_trends.png` - trendy tematów kluczowych.
- `03_topic_cooccurrence.png` - heatmapa współwystępowania tematów.

## `notebooks/`

- `01_openalex_data_collection.ipynb` - starszy notebook użyty do pierwotnego pobierania danych z OpenAlex.
