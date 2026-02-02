from cbz_tagger.entities.chapter_plugins.html_scraper import HtmlScraper
from cbz_tagger.entities.chapter_plugins.plugin import ChapterPluginEntity


class HtmlChapterPluginEntity(ChapterPluginEntity):
    """Base class for HTML-scraping chapter plugins.

    Extends ChapterPluginEntity with utilities for fetching and parsing HTML pages.
    Use this as the base class when the source provides HTML pages rather than
    JSON APIs.
    """

    @classmethod
    def fetch_and_parse(cls, url: str) -> HtmlScraper:
        """Fetch a URL and return an HtmlScraper for parsing.

        Args:
            url: The URL to fetch

        Returns:
            HtmlScraper instance ready for parsing
        """
        response = cls.request_with_retry(url)
        return HtmlScraper.from_response(response)
