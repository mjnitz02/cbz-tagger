import re
from typing import Any

from bs4 import BeautifulSoup
from bs4.element import PageElement
from bs4.element import Tag


class HtmlScraper:
    """Utility class for HTML parsing with convenient helper methods."""

    def __init__(self, html: str):
        """Initialize the scraper with HTML content.

        Args:
            html: Raw HTML string to parse
        """
        self.soup = BeautifulSoup(html, "html.parser")

    @classmethod
    def from_response(cls, response) -> "HtmlScraper":
        """Create an HtmlScraper from a requests Response object.

        Args:
            response: A requests Response object with .text attribute

        Returns:
            HtmlScraper instance
        """
        return cls(response.text)

    def find_one_safe(self, tag: str, attrs: dict[str, Any], error_msg: str) -> Tag:
        """Find a single element, raising an error if not found.

        Args:
            tag: HTML tag name to find
            attrs: Dictionary of attributes to match
            error_msg: Error message if element not found

        Returns:
            The first matching BeautifulSoup Tag

        Raises:
            EnvironmentError: If no matching element is found
        """
        elements = self.soup.find_all(tag, attrs)
        if len(elements) == 0:
            raise EnvironmentError(error_msg)
        result = elements[0]
        assert isinstance(result, Tag), f"Expected Tag, got {type(result)}"
        return result

    def find_all_safe(self, tag: str, attrs: dict[str, Any], error_msg: str) -> list[PageElement]:
        """Find all matching elements, raising an error if none found.

        Args:
            tag: HTML tag name to find
            attrs: Dictionary of attributes to match
            error_msg: Error message if no elements found

        Returns:
            List of matching BeautifulSoup elements

        Raises:
            EnvironmentError: If no matching elements are found
        """
        elements = self.soup.find_all(tag, attrs)
        if len(elements) == 0:
            raise EnvironmentError(error_msg)
        return list(elements)

    def find_all(self, tag: str, attrs: dict[str, Any] | None = None) -> list[PageElement]:
        """Find all matching elements without error checking.

        Args:
            tag: HTML tag name to find
            attrs: Optional dictionary of attributes to match

        Returns:
            List of matching BeautifulSoup elements (may be empty)
        """
        if attrs is None:
            return list(self.soup.find_all(tag))
        return list(self.soup.find_all(tag, attrs))

    def extract_script_variable(self, var_name: str, error_msg: str) -> str:
        """Extract the value of a JavaScript variable from script tags.

        Searches all <script> tags for a pattern like:
        var varName = "value";

        Args:
            var_name: Name of the JavaScript variable to find
            error_msg: Error message if variable not found

        Returns:
            The string value of the variable (without quotes)

        Raises:
            EnvironmentError: If variable is not found in any script tag
        """
        script_elements = self.soup.find_all("script")
        for script in script_elements:
            if not isinstance(script, Tag):
                continue
            script_text = script.text
            if f"var {var_name}" in script_text:
                # Match patterns like: var varName = "value"; or var varName = 'value';
                pattern = rf'var\s+{re.escape(var_name)}\s*=\s*["\']([^"\']*)["\'];?'
                match = re.search(pattern, script_text)
                if match:
                    return match.group(1)
        raise EnvironmentError(error_msg)
