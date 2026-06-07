import scrapy


class WebPracticeSourceItem(scrapy.Item):
    """Jednolity rekord webowy zapisywany potem do CSV.

    Scrapy pobiera strony HTML, ale analiza EDA oczekuje danych podobnych do
    eksportów z OpenAlex/Crossref/PubMed. Ten item jest mostem między tymi
    światami: każda strona webowa dostaje tytuł, rok, źródło i pola pomocnicze.
    """

    # Pola wymagane przez aktualny pipeline EDA.
    title = scrapy.Field()
    year = scrapy.Field()
    citations = scrapy.Field()

    # Pola opisowe, które pomagają w ręcznej interpretacji źródeł webowych.
    abstract = scrapy.Field()
    source_database = scrapy.Field()
    source = scrapy.Field()
    url = scrapy.Field()
    query_group = scrapy.Field()

    # Pola zgodności ze schematem publikacji naukowych. Dla stron webowych
    # zwykle pozostają puste, ale dzięki nim CSV łatwo scala się z resztą danych.
    doi = scrapy.Field()
    external_id = scrapy.Field()
    authors = scrapy.Field()
    topics = scrapy.Field()
