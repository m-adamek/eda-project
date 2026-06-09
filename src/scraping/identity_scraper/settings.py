BOT_NAME = "identity_scraper"


SPIDER_MODULES = ["src.scraping.identity_scraper.spiders"]
NEWSPIDER_MODULE = "src.scraping.identity_scraper.spiders"


ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 4
DOWNLOAD_DELAY = 1.0

# Crawling ma zbierać dane w skali większej niż ręczna kwerenda, ale nadal
# kontrolowanie. AutoThrottle spowalnia spidera, jeśli serwer odpowiada wolniej.
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 8.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

DEPTH_LIMIT = 3


USER_AGENT = (
    "identity-overlay-eda academic metadata collector "
    "(polite Scrapy bot; contact configured by project user)"
)


FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = "INFO"

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
