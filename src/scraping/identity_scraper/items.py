import scrapy


class ProductChangelogItem(scrapy.Item):
    """One product-release or changelog entry.

    The row is intentionally simple: year + product + feature description. The
    analysis layer later detects features such as pronouns, chosen/preferred
    names and gender fields.
    """

    source_type = scrapy.Field()
    product = scrapy.Field()
    source = scrapy.Field()
    year = scrapy.Field()
    date = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    feature_terms = scrapy.Field()
    url = scrapy.Field()
    source_url = scrapy.Field()
    crawl_depth = scrapy.Field()


class ConferenceSessionItem(scrapy.Item):
    """One HR/IT/IAM conference session entry."""

    source_type = scrapy.Field()
    event_name = scrapy.Field()
    source = scrapy.Field()
    year = scrapy.Field()
    session_title = scrapy.Field()
    abstract = scrapy.Field()
    topic_terms = scrapy.Field()
    url = scrapy.Field()
    source_url = scrapy.Field()
    crawl_depth = scrapy.Field()
