import os


class Mode(object):
    AUTO = "auto"
    MANUAL = "manual"
    RETAG = "retag"
    UPDATE = "update"


class ContainerMode(object):
    TIMER = "timer"
    CONTINUOUS = "timer"
    MANUAL = "timer"


class AppEnv(object):
    if os.getenv("CONFIG_PATH") is not None:
        config_path = os.getenv("CONFIG_PATH")
    else:
        config_path = "\\config"

    if os.getenv("DOWNLOADS_PATH") is not None:
        downloads_path = os.getenv("DOWNLOADS_PATH")
    else:
        downloads_path = "\\downloads"

    timer_mode = os.getenv("ENABLE_TIMER_MODE") == "true"
    continuous_mode = os.getenv("ENABLE_CONTINUOUS_MODE") == "true"

    if os.getenv("TIMER_MODE_DELAY") is None:
        timer_mode_delay = 600
    else:
        timer_mode_delay = int(os.getenv("TIMER_MODE_DELAY"))


class MetadataSource(object):
    url = "https://anilist.co/manga/{}"

    access = {
        "header": {
            "Content-Type": "application/json",
            "User-Agent": "AnilistPython (github.com/ReZeroE/AnilistPython)",
            "Accept": "application/json",
        },
        "authurl": "https://anilist.co/api",
        "apiurl": "https://graphql.anilist.co",
        "cid": None,
        "csecret": None,
        "token": None,
    }

    query_id = """\
        query ($query: String, $page: Int, $perpage: Int) {
            Page (page: $page, perPage: $perpage) {
                pageInfo {
                    total
                    currentPage
                    lastPage
                    hasNextPage
                }
                media (search: $query, type: MANGA) {
                    id
                    title {
                        romaji
                        english
                    }
                    popularity
                    chapters
                    format
                }
            }
        }
    """

    query_info = """\
            query ($id: Int) {
                Media(id: $id, type: MANGA) {
                    title {
                        romaji
                        english
                    }
                    startDate {
                        year
                        month
                        day
                    }
                    endDate {
                        year
                        month
                        day
                    }
                    coverImage {
                        large
                    }
                    tags {
                        name
                    }
                    staff {
                        edges {
                            node{
                                name {
                                    first
                                    last
                                    full
                                    alternative
                                }
                                siteUrl
                            }
                            role
                        }
                    }
                    bannerImage
                    format
                    chapters
                    volumes
                    status
                    description
                    averageScore
                    meanScore
                    genres
                    synonyms
                }
            }
        """
