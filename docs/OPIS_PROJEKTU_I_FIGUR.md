# Opis projektu, wyszukiwań i figur

## Cel projektu

Projekt przygotowuje eksploracyjną analizę literatury pod artykuł o projektowaniu systemów informatycznych wspierających inkluzywność, szczególnie o reprezentacji tożsamości użytkownika, rozdzieleniu `legal identity` i `display identity` oraz koncepcji `Identity Overlay`.

## Główne pliki kodu

### `main.py`

- Punkt wejścia do analizy.
- Uruchamia `run_analysis()` z modułu `src/analysis/identity_overlay_eda.py`.

### `src/api/query_plan.py`

- Definiuje wspólne grupy zapytań dla wszystkich źródeł.
- Grupy obejmują: `identity_overlay_core`, `transgender_organizational_systems`, `iam_architecture`, `inclusive_design_values`, `relational_legal_status`.
- Tu należy zmieniać lub dodawać słowa kluczowe, jeśli zakres wyszukiwania ma być szerszy albo węższy.

### `src/api/openalex_identity_overlay.py`

- Pobiera dane z OpenAlex.
- Zapisuje wynik do `data/raw/openalex_identity_overlay_targeted.csv`.
- Pobiera m.in. tytuł, rok, cytowania, DOI, autorów, tematy OpenAlex i abstrakt rekonstruowany z indeksu OpenAlex.

### `src/api/crossref_identity_overlay.py`

- Pobiera dane z Crossref.
- Zapisuje wynik do `data/raw/crossref_identity_overlay_targeted.csv`.
- Crossref jest użyteczny do metadanych wydawniczych, DOI, czasopism i liczby referencji/cytowań raportowanej przez Crossref.

### `src/api/pubmed_identity_overlay.py`

- Pobiera dane z PubMed przez NCBI E-utilities.
- Zapisuje wynik do `data/raw/pubmed_identity_overlay_targeted.csv`.
- Najbardziej przydatne dla publikacji medycznych, psychologicznych i zdrowotnych dotyczących osób transpłciowych, dyskryminacji, zdrowia i doświadczeń użytkowników.

### `src/api/collect_all_sources.py`

- Uruchamia wszystkie kolektory: OpenAlex, Crossref i PubMed.
- Przykład:

```powershell
.\.venv\Scripts\python.exe -m src.api.collect_all_sources --email twoj-email@example.com
```

### `src/analysis/identity_overlay_eda.py`

- Ładuje wszystkie pliki `data/raw/*identity_overlay*.csv`.
- Jeśli nie ma takich plików albo są puste, wraca do starego zbioru `data/raw/openalex_workplace_inclusion.csv`.
- Scala źródła, deduplikuje rekordy po DOI albo po parze tytuł + rok.
- Oznacza publikacje flagami tematycznymi zgodnymi z draftem artykułu.
- Generuje tabele w `data/processed/` i figury w `visuals/`.

## Dane i wyniki

### `data/raw/openalex_workplace_inclusion.csv`

- Stary lokalny zbiór OpenAlex o inkluzywności w środowisku pracy.
- Służy jako fallback, jeśli nie pobrano nowych danych wieloźródłowych.

### `data/processed/identity_overlay_enriched.csv`

- Aktualny główny plik wynikowy.
- Zawiera rekordy publikacji po scaleniu/deduplikacji oraz flagi tematów.

### `data/processed/source_summary.csv`

- Podsumowuje liczbę rekordów według bazy źródłowej.
- Aktualnie po pobraniu i deduplikacji: OpenAlex 19 571 rekordów, Crossref 5 107 rekordów, PubMed 100 rekordów.

### `data/processed/topic_summary.csv`

- Podsumowuje liczbę publikacji w każdej kategorii tematycznej.
- Pomaga pokazać, które obszary literatury są najsilniej reprezentowane.
- Aktualnie analiza obejmuje 24 778 rekordów z lat 2000-2025.

### `data/processed/topic_year_counts.csv`

- Liczba publikacji rocznie dla każdej kategorii tematycznej.
- Ten plik jest podstawą figury `02_topic_trends.png`.

### `data/processed/topic_cooccurrence.csv`

- Macierz współwystępowania tematów.
- Pokazuje, które kategorie pojawiają się razem w tytułach i abstraktach.

### `data/processed/top_relevant_articles.csv`

- Lista publikacji najlepiej pasujących do ramy artykułu.
- Służy do ręcznego przeglądu literatury i wyboru pozycji do cytowania.

## Figury

### `visuals/01_publication_trend.png`

- Pokazuje roczną liczbę publikacji w analizowanym zbiorze oraz średnią kroczącą 3-letnią.
- Nadaje się do pokazania ogólnego rozwoju zainteresowania tematyką inkluzywności, reprezentacji tożsamości i systemów organizacyjnych.

### `visuals/02_topic_trends.png`

- Pokazuje trendy roczne dla kluczowych tematów artykułu: `identity_representation`, `transgender_workplace_experience`, `iam_and_architecture`, `hr_and_organizational_systems`, `inclusive_design_and_vsd`.
- Pomaga porównać, czy literatura organizacyjno-inkluzywna rozwija się razem z literaturą techniczną dotyczącą IAM.

### `visuals/03_topic_cooccurrence.png`

- Heatmapa współwystępowania tematów.
- Najważniejsza dla tezy o luce badawczej: pokazuje, czy terminy społeczne, projektowe i techniczne pojawiają się w tych samych publikacjach.

## Ocena kodu po sprawdzeniu

- Struktura jest modułowa: zapytania są oddzielone od kolektorów, a analiza od pobierania danych.
- Kolektory zapisują wspólny schemat kolumn, więc dane z różnych baz można połączyć.
- Kolektory są odporne na pojedyncze błędy API: nieudane zapytanie zwraca pustą listę i nie przerywa całego procesu.
- Puste eksporty nadal mają nagłówki i nie powinny psuć analizy.
- Analiza deduplikuje publikacje po DOI albo po tytule i roku.

## Najważniejsze ograniczenia

- Klasyfikacja tematów jest słownikowa, więc ma charakter eksploracyjny, a nie pełnotekstowy.
- PubMed nie dostarcza liczby cytowań w tym kolektorze, więc pole `citations` dla PubMed ma wartość `0`.
- Crossref i PubMed są pobierane przez API; to kontrolowane pobieranie metadanych, nie klasyczny scraping HTML stron.
