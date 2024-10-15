from time import sleep
from typing import List

from cbz_tagger.entities.chapter_entity import ChapterEntity


class ChapterEntityMangaDex(ChapterEntity):
    entity_url: str = f"{ChapterEntity.base_url}/manga"
    download_url: str = f"{ChapterEntity.base_url}/at-home/server"

    @classmethod
    def from_server_url(cls, query_params=None):
        entity_id = query_params["ids[]"][0]

        order = {
            "createdAt": "asc",
            "updatedAt": "asc",
            "publishAt": "asc",
            "readableAt": "asc",
            "volume": "asc",
            "chapter": "asc",
        }
        params = "&".join([f"order%5B{key}%5D={value}" for key, value in order.items()])
        response = cls.unpaginate_request(f"{cls.entity_url}/{entity_id}/feed?{params}")
        return [cls(data) for data in response]

    def get_chapter_url(self):
        url = f"{self.download_url}/{self.entity_id}"
        return url

    def parse_chapter_download_links(self, url: str) -> List[str]:
        response = self.request_with_retry(url).json()

        # If we didn't retrieve enough pages, try to query again
        if len(response["chapter"][self.quality]) != self.pages:
            print("Not enough pages returned from server. Waiting 10s and retrying query.")
            sleep(10)
            response = self.request_with_retry(url).json()
            if len(response["chapter"][self.quality]) != self.pages:
                raise EnvironmentError(
                    f"Failed to download chapter {self.entity_id}, not enough pages returned from server"
                )

        base_url = f"{response['baseUrl']}/{self.quality}/{response['chapter']['hash']}"
        links = []
        for chapter_image_name in response["chapter"][self.quality]:
            links.append(f"{base_url}/{chapter_image_name}")
        return links
