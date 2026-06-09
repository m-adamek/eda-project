# Zamysł scrapingu

Scraping w projekcie ma teraz dwa osobne cele badawcze.

## 1. Changelogi produktów

Pierwszy crawler zbiera release notes i changelogi produktów organizacyjnych:

- Microsoft 365,
- Google Workspace,
- Slack,
- Workday.

Spider `product_changelogs` pobiera:

- rok,
- produkt,
- tytuł wpisu,
- opis funkcji lub zmiany,
- URL źródłowy,
- wykryte terminy funkcji, np. pronouns, preferred/chosen names, gender fields.

Cel: sprawdzić, kiedy w komunikacji produktowej pojawiają się funkcje związane z
reprezentacją tożsamości użytkownika, np. zaimki, preferowane imię, wyświetlana
nazwa albo pola płci/tożsamości płciowej.

Przykładowy efekt analizy:

| Rok | Produkt | Funkcja |
| --- | --- | --- |
| 2021 | Slack | pronouns |
| 2022 | Google Workspace | preferred/chosen names |
| 2023 | Workday | gender fields |

## 2. Konferencje i wydarzenia HR/IT/IAM

Drugi crawler zbiera programy konferencji, archiwa sesji i strony wydarzeń:

- Gartner Identity & Access Management Summit,
- Identiverse,
- RSA/RSAC Conference,
- HR Technology Conference.

Spider `conference_sessions` pobiera:

- rok,
- nazwę wydarzenia,
- tytuł sesji,
- abstrakt lub opis sesji,
- URL źródłowy,
- wykryte tematy, np. identity management, identity representation, HR tech, AI.

Cel: sprawdzić, jak zmienia się język wydarzeń branżowych w czasie. Taki zbiór
pozwala porównać wcześniejszą dominację tematów typu `identity management` z
nowszymi tematami typu `identity representation`, `AI identity`, `human identity`
albo `inclusive HR technology`.

Przykładowy efekt analizy:

| Rok | Dominujący język |
| --- | --- |
| 2010 | identity management |
| 2025 | identity representation / AI identity |

## Komendy

Changelogi produktów:

```powershell
.\.venv\Scripts\scrapy.exe crawl product_changelogs
```

Większy crawl changelogów:

```powershell
.\.venv\Scripts\scrapy.exe crawl product_changelogs -a max_depth=3 -a max_pages=3000
```

Konferencje:

```powershell
.\.venv\Scripts\scrapy.exe crawl conference_sessions
```

Większy crawl konferencji:

```powershell
.\.venv\Scripts\scrapy.exe crawl conference_sessions -a max_depth=3 -a max_pages=4000
```

Analiza wyników scrapingu:

```powershell
.\.venv\Scripts\python.exe -m src.analysis.scraping_timeline_analysis
```
