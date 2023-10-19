class Mode:
    AUTO = "auto"
    MANUAL = "manual"
    RETAG = "retag"
    UPDATE = "update"

class ContainerMode:
    TIMER = "timer"
    MANUAL = "manual"


class MetadataSource:
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
