BOT_NAME = "identity_scraper"

# Scrapy szuka spiderów w tym pakiecie. Ścieżki są pełne, bo projekt Scrapy
# działa wewnątrz zwykłego pakietu `src`, a nie jako osobne repozytorium.
SPIDER_MODULES = ["src.scraping.identity_scraper.spiders"]
NEWSPIDER_MODULE = "src.scraping.identity_scraper.spiders"

# Te ustawienia trzymają crawler w trybie grzecznego pobierania:
# respektujemy robots.txt, ograniczamy równoległość i robimy pauzę między
# requestami, aby nie obciążać stron dokumentacji.
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 4
DOWNLOAD_DELAY = 1.0

# User agent jasno mówi, że to akademicki kolektor metadanych, a nie crawler
# produkcyjny ani bot próbujący masowo indeksować strony.
USER_AGENT = (
    "identity-overlay-eda academic metadata collector "
    "(polite Scrapy bot; contact configured by project user)"
)

# Eksport CSV ma być stabilny i czytelny w pandas/Excelu.
FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = "INFO"

# Ustawienia zgodności z aktualnym Scrapy/Twisted.
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
