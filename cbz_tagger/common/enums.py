import base64

APPLICATION_MAJOR_VERSION = 4


IgnoredTags = {
    "ddefd648-5140-4e5f-ba18-4eca4071d19b",
    "2d1f5d56-a1e5-4d0d-a961-2193588b08ec",
}


class Urls:
    MDX: str = base64.b64decode("bWFuZ2FkZXgub3Jn").decode("utf-8")


class Status:
    ONGOING: str = "ongoing"
    COMPLETED: str = "completed"
    HIATUS: str = "hiatus"
    CANCELLED: str = "cancelled"
    DROPPED: str = "dropped"
