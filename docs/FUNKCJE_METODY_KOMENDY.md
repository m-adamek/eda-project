# Funkcje, metody i komendy

Krótki katalog elementów używanych w projekcie. Podział jest według biblioteki
albo narzędzia, z którego dany element pochodzi.

## Komendy projektu

- `.\.venv\Scripts\python.exe main.py` - uruchamia pełną analizę EDA.
- `.\.venv\Scripts\python.exe -m src.api.openalex_identity_overlay` - pobiera dane z OpenAlex.
- `.\.venv\Scripts\python.exe -m src.api.crossref_identity_overlay` - pobiera dane z Crossref.
- `.\.venv\Scripts\python.exe -m src.api.pubmed_identity_overlay` - pobiera dane z PubMed.
- `.\.venv\Scripts\python.exe -m src.api.collect_all_sources --email your-email@example.com` - uruchamia trzy kolektory API w jednym przebiegu.
- `.\.venv\Scripts\scrapy.exe crawl product_changelogs` - pobiera changelogi i release notes produktów.
- `.\.venv\Scripts\scrapy.exe crawl product_changelogs -a max_depth=3 -a max_pages=3000` - uruchamia większy crawl changelogów.
- `.\.venv\Scripts\scrapy.exe crawl conference_sessions` - pobiera programy konferencji i archiwa sesji.
- `.\.venv\Scripts\scrapy.exe crawl conference_sessions -a max_depth=3 -a max_pages=4000` - uruchamia większy crawl konferencji.
- `.\.venv\Scripts\python.exe -m src.analysis.scraping_timeline_analysis` - analizuje wyniki scrapingu i tworzy tabele trendów.
- `.\.venv\Scripts\python.exe -m py_compile ...` - sprawdza składnię wskazanych plików Pythona.

## Funkcje projektu

### `main.py`

- `main()` - wywołuje `run_analysis()` i jest głównym punktem startowym projektu.

### `src/api/query_plan.py`

- `iter_queries()` - zwraca kolejne pary `(query_group, query)` ze wspólnego planu zapytań.
- `QUERY_GROUPS` - słownik grup tematycznych i zapytań badawczych.
- `OUTPUT_COLUMNS` - wspólny schemat kolumn dla eksportów API.

### `src/api/openalex_identity_overlay.py`

- `_reconstruct_abstract()` - odtwarza abstrakt OpenAlex z inverted index.
- `_extract_authorships()` - wyciąga autorów z rekordu OpenAlex.
- `_extract_topics()` - wyciąga tematy OpenAlex.
- `fetch_query_group()` - pobiera wyniki OpenAlex dla jednej grupy i jednego zapytania.
- `_safe_fetch_query_group()` - obsługuje błędy HTTP i zwraca pustą listę przy nieudanym zapytaniu.
- `collect_identity_overlay_dataset()` - pobiera pełny zestaw OpenAlex i zapisuje CSV.

### `src/api/crossref_identity_overlay.py`

- `_first()` - pobiera pierwszy element z list Crossref albo zwraca prostą wartość.
- `_published_year()` - ustala rok publikacji z pól dat Crossref.
- `_clean_abstract()` - usuwa HTML/XML z abstraktu Crossref.
- `_authors()` - składa autorów Crossref do tekstu rozdzielonego średnikami.
- `fetch_query_group()` - pobiera wyniki Crossref dla jednej grupy i jednego zapytania.
- `_safe_fetch_query_group()` - obsługuje błędy HTTP Crossref.
- `collect_identity_overlay_dataset()` - pobiera pełny zestaw Crossref i zapisuje CSV.

### `src/api/pubmed_identity_overlay.py`

- `_text()` - pobiera tekst z elementu XML PubMed.
- `_article_year()` - ustala rok publikacji z rekordu XML.
- `_authors()` - składa autorów PubMed do tekstu.
- `_mesh_terms()` - zbiera terminy MeSH.
- `_search_pubmed_ids()` - wykonuje `esearch` i pobiera listę PMID.
- `_fetch_pubmed_records()` - wykonuje `efetch` i pobiera szczegóły rekordów XML.
- `fetch_query_group()` - łączy wyszukiwanie PMID i pobieranie metadanych.
- `_safe_fetch_query_group()` - obsługuje błędy HTTP i błędy parsowania XML.
- `collect_identity_overlay_dataset()` - pobiera pełny zestaw PubMed i zapisuje CSV.

### `src/api/collect_all_sources.py`

- `main()` - czyta argumenty CLI i uruchamia kolektory OpenAlex, Crossref oraz PubMed.

### `src/analysis/identity_overlay_eda.py`

- `_keyword_pattern()` - buduje regex dla słowa lub frazy tematycznej.
- `discover_publication_files()` - znajduje pliki `*identity_overlay*.csv` albo fallback legacy.
- `_dedupe_publications()` - usuwa duplikaty po DOI albo po tytule i roku.
- `load_publications()` - ładuje i normalizuje dane publikacji.
- `add_topic_flags()` - dodaje kolumny True/False dla kategorii tematycznych.
- `build_topic_summary()` - tworzy tabelę podsumowania tematów.
- `build_topic_year_counts()` - tworzy liczniki tematów według lat.
- `build_cooccurrence()` - tworzy macierz współwystępowania tematów.
- `build_top_articles()` - wybiera rekordy najbardziej trafne do ręcznego screeningu.
- `save_visuals()` - zapisuje wykresy PNG.
- `run_analysis()` - wykonuje cały pipeline analityczny.

### `src/analysis/scraping_timeline_analysis.py`

- `_load_csv()` - wczytuje wynik scrapingu albo zwraca pustą tabelę o wymaganym schemacie.
- `_matches_any()` - sprawdza, czy tekst pasuje do dowolnego wzorca regex.
- `_matched_labels()` - zwraca etykiety funkcji lub tematów wykryte w tekście.
- `analyse_product_changelogs()` - tworzy timeline funkcji produktowych i tabelę first-seen.
- `analyse_conference_sessions()` - tworzy trendy tematów konferencji i dominanty roczne.
- `run_scraping_timeline_analysis()` - zapisuje wszystkie tabele wynikowe do `data/processed/`.

### `src/scraping/identity_scraper/items.py`

- `ProductChangelogItem` - schemat rekordu Scrapy dla release notes/changelogów.
- `ConferenceSessionItem` - schemat rekordu Scrapy dla sesji konferencyjnych.

### `src/scraping/identity_scraper/spiders/product_changelogs.py`

- `ProductChangelogsSpider` - crawler release notes i changelogów produktów.
- `__init__()` - ustawia domyślny albo alternatywny plik seedów.
- `start_requests()` - czyta seed CSV i tworzy requesty startowe Scrapy.
- `parse_release_page()` - wyciąga rok, tytuł i opis funkcji ze strony changeloga.
- `_extract_entries()` - dzieli stronę release notes na kandydatów wpisów.
- `_follow_relevant_links()` - przechodzi po linkach wewnętrznych, dopóki nie zostaną osiągnięte limity.
- `_matched_features()` - wykrywa funkcje typu pronouns, chosen names i gender fields.
- `_should_follow()` - decyduje, czy link wygląda jak release note/changelog.

### `src/scraping/identity_scraper/spiders/conference_sessions.py`

- `ConferenceSessionsSpider` - crawler programów konferencji i archiwów sesji.
- `parse_event_page()` - wyciąga tytuły sesji, abstrakty i rok.
- `_extract_sessions()` - znajduje bloki wyglądające jak sesje konferencyjne.
- `_matched_topics()` - klasyfikuje sesje do tematów, np. identity management albo AI.
- `_should_follow()` - decyduje, czy link wygląda jak agenda, program, sesja lub archiwum.

## Python standard library

- `argparse.ArgumentParser()` - definiuje opcje komend CLI.
- `Path()` / `Path.mkdir()` / `Path.glob()` / `Path.exists()` / `Path.open()` - obsługa ścieżek i plików.
- `csv.DictReader()` - czyta CSV jako słowniki.
- `datetime.now()` - ustala bieżący rok dla zakresu analizy.
- `itertools.combinations()` - tworzy pary tematów do macierzy współwystępowania.
- `re.compile()` / `re.escape()` / `re.findall()` / `re.sub()` - praca z wyrażeniami regularnymi.
- `time.sleep()` - pauza między zapytaniami do API.
- `xml.etree.ElementTree.fromstring()` / `Element.find()` / `Element.findall()` / `Element.itertext()` - parsowanie XML PubMed.

## `requests`

- `requests.get()` - wykonuje zapytanie HTTP GET do API.
- `response.raise_for_status()` - przerywa przy błędach HTTP.
- `response.json()` - zamienia odpowiedź JSON na struktury Pythona.
- `response.text` - pobiera surowy tekst odpowiedzi, używany przy XML PubMed.
- `requests.RequestException` - typ błędu obsługiwany w bezpiecznych wrapperach.

## `pandas`

- `pd.read_csv()` - wczytuje CSV do DataFrame.
- `pd.DataFrame()` - tworzy tabelę danych.
- `pd.concat()` - łączy wiele tabel.
- `pd.to_numeric()` - konwertuje kolumny na liczby.
- `DataFrame.dropna()` - usuwa wiersze z brakującymi wartościami.
- `DataFrame.drop_duplicates()` - usuwa duplikaty.
- `DataFrame.sort_values()` - sortuje tabelę.
- `DataFrame.groupby()` - grupuje dane do agregacji.
- `DataFrame.agg()` - liczy wiele agregacji jednocześnie.
- `DataFrame.reset_index()` - przywraca indeks jako kolumnę.
- `DataFrame.to_csv()` - zapisuje tabelę do CSV.
- `Series.fillna()` / `Series.astype()` / `Series.str.*` - czyszczenie kolumn tekstowych.
- `Series.rolling().mean()` - liczy średnią kroczącą.

## `matplotlib` i `seaborn`

- `sns.set_theme()` - ustawia styl wykresów.
- `sns.lineplot()` - rysuje wykres liniowy.
- `sns.heatmap()` - rysuje heatmapę.
- `plt.figure()` - tworzy figurę.
- `plt.title()` / `plt.xlabel()` / `plt.ylabel()` / `plt.legend()` - opisuje wykres.
- `plt.tight_layout()` - poprawia rozmieszczenie elementów.
- `plt.savefig()` - zapisuje wykres do PNG.
- `plt.close()` - zamyka figurę po zapisie.
- `LinearSegmentedColormap.from_list()` - tworzy własną paletę kolorów.

## `BeautifulSoup`

- `BeautifulSoup(value, "html.parser")` - parsuje HTML/XML z abstraktu Crossref.
- `get_text(" ", strip=True)` - zwraca czysty tekst bez tagów.

## `tqdm`

- `tqdm(total=..., desc=...)` - pokazuje pasek postępu.
- `progress.update(1)` - przesuwa pasek po wykonaniu zapytania.

## `Scrapy`

- `scrapy.Item` - bazowa klasa rekordu danych.
- `scrapy.Field()` - deklaruje pole w itemie.
- `scrapy.Spider` - bazowa klasa spidera.
- `scrapy.Request()` - tworzy request HTTP.
- `response.css()` - wybiera elementy HTML selektorami CSS.
- `selector.get()` / `selector.getall()` - pobiera tekst albo atrybuty z selektora.
- `custom_settings["FEEDS"]` - ustawia eksport wyniku spidera do CSV.
- `AUTOTHROTTLE_ENABLED` - dopasowuje tempo crawlowania do odpowiedzi serwera.
- `CLOSESPIDER_PAGECOUNT` - zatrzymuje spider po osiągnięciu limitu pobranych stron.
- `DEPTH_LIMIT` - ogranicza głębokość przechodzenia po linkach.

## `pip`, `uv` i konfiguracja

- `pip install -r requirements.txt` - instaluje zależności z listy.
- `pyproject.toml` - opisuje projekt i zależności dla nowoczesnych narzędzi Pythona.
- `uv.lock` - zamraża dokładny zestaw zależności, jeśli projekt jest obsługiwany przez `uv`.
- `scrapy.cfg` - mówi Scrapy, gdzie są ustawienia projektu.
