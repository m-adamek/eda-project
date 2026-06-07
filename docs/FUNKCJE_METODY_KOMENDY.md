# Funkcje, metody i komendy

Krótki katalog elementów używanych w projekcie. Podział jest według biblioteki
albo narzędzia, z którego dany element pochodzi.

## Komendy projektu

- `.\.venv\Scripts\python.exe main.py` - uruchamia pełną analizę EDA.
- `.\.venv\Scripts\python.exe -m src.api.openalex_identity_overlay` - pobiera dane z OpenAlex.
- `.\.venv\Scripts\python.exe -m src.api.crossref_identity_overlay` - pobiera dane z Crossref.
- `.\.venv\Scripts\python.exe -m src.api.pubmed_identity_overlay` - pobiera dane z PubMed.
- `.\.venv\Scripts\python.exe -m src.api.collect_all_sources --email your-email@example.com` - uruchamia trzy kolektory API w jednym przebiegu.
- `.\.venv\Scripts\scrapy.exe crawl web_practice_sources` - uruchamia Scrapy dla listy `data/raw/scrapy_seed_urls.csv`.
- `.\.venv\Scripts\scrapy.exe crawl web_practice_sources -a seeds=ścieżka\do\seedów.csv` - uruchamia Scrapy na alternatywnej liście URL-i.
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

### `src/scraping/identity_scraper/items.py`

- `WebPracticeSourceItem` - schemat rekordu Scrapy zgodny z CSV używanym w EDA.

### `src/scraping/identity_scraper/spiders/web_practice_sources.py`

- `WebPracticeSourcesSpider` - spider Scrapy dla ręcznie dobranych stron webowych.
- `__init__()` - ustawia domyślny albo alternatywny plik seedów.
- `start_requests()` - czyta seed CSV i tworzy requesty Scrapy.
- `parse_page()` - wyciąga tytuł, opis, rok i metadane strony.
- `_first_text()` - zwraca pierwszą niepustą wartość z listy selektorów CSS.
- `_clean()` - normalizuje białe znaki w tekście.
- `_extract_year()` - szuka roku w tekście lub URL-u.
- `_parse_seed_year()` - waliduje rok wpisany w seed CSV.
- `_domain_label()` - robi krótką etykietę źródła z domeny URL.

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

## `pip`, `uv` i konfiguracja

- `pip install -r requirements.txt` - instaluje zależności z listy.
- `pyproject.toml` - opisuje projekt i zależności dla nowoczesnych narzędzi Pythona.
- `uv.lock` - zamraża dokładny zestaw zależności, jeśli projekt jest obsługiwany przez `uv`.
- `scrapy.cfg` - mówi Scrapy, gdzie są ustawienia projektu.
