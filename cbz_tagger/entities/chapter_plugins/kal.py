from typing import Any
from typing import List

from bs4 import BeautifulSoup

from cbz_tagger.common.enums import Plugins
from cbz_tagger.common.enums import Urls
from cbz_tagger.entities.chapter_plugins.plugin import ChapterPluginEntity


class ChapterPluginKAL(ChapterPluginEntity):
    entity_url = f"https://{Urls.KAL}"

    @classmethod
    def parse_info_feed(cls, entity_id: str) -> List[Any]:
        url = f"{cls.entity_url}/manga/{entity_id}"
        response = cls.request_with_retry(url)

        soup = BeautifulSoup(response.text, "html.parser")
        chapter_entity = soup.find_all("ul", class_="chapter-list")
        items = chapter_entity[0].find_all("li")

        content = []
        # This constructs an api compatible response from the rss feed
        for item in items:
            chapter_number_str = item.get("id")[2:]
            item_content = item.find_all("a", href=True)[0]
            chapter_id = str(item_content.get("href").split("manga/")[-1]).replace("/", "-")
            link = f"{cls.entity_url}{str(item_content.get('href'))}"
            chapter_title = item_content.find_all("strong", class_="chapter-title")[0].text
            updated = None
            content.append(
                {
                    "id": f"{entity_id}-{chapter_id}".lower(),
                    "type": Plugins.KAL,
                    "attributes": {
                        "title": chapter_title,
                        "url": link,
                        "chapter": chapter_number_str,
                        "translatedLanguage": "en",
                        "pages": -1,
                        "volume": -1,
                        "updatedAt": updated,
                    },
                }
            )
        return content

    def parse_chapter_download_links(self, url: str) -> List[str]:
        response = self.request_with_retry(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the root url for the chapter
        script_elements = soup.find_all("script")
        chapter_images = None
        for script in script_elements:
            if "var chapImages" in script.text:
                chapter_images = script.text
                break

        if chapter_images is None:
            raise EnvironmentError("Could not find chapter images")

        chapter_images = chapter_images.strip().replace('var chapImages = "', "")
        pages = chapter_images.split(",")

        links = []
        for page in pages:
            links.append(page.strip())
        return links
