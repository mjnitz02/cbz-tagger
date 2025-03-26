import base64

APPLICATION_MAJOR_VERSION = 3
DELAY_PER_REQUEST = 0.3


class Mode:
    AUTO = "auto"
    MANUAL = "manual"
    RETAG = "retag"
    UPDATE = "update"


class ContainerMode:
    TIMER: str = "timer"
    MANUAL: str = "manual"
    GUI: str = "gui"


class Urls:
    MDX = base64.b64decode("bWFuZ2FkZXgub3Jn").decode("utf-8")
    CMK = base64.b64decode("YXBpLmNvbWljay5mdW4=").decode("utf-8")
    CMK_TITLE = base64.b64decode("Y29taWNrLmlv").decode("utf-8")
    WBC = base64.b64decode("d2VlYmNlbnRyYWwuY29t").decode("utf-8")
    KAL = base64.b64decode("a2FsaXNjYW4uaW8=").decode("utf-8")


class Plugins:
    MDX = "mdx"
    CMK = "cmk"
    WBC = "wbc"
    KAL = "kal"

    TITLE_URLS = {
        MDX: f"https://{Urls.MDX}/title/",
        CMK: f"https://{Urls.CMK_TITLE}/comic/",
        WBC: f"https://{Urls.WBC}/series/",
        KAL: f"https://{Urls.WBC}/manga/",
    }

    @classmethod
    def all(cls):
        return [cls.MDX, cls.CMK, cls.WBC]


class Status:
    ONGOING = "ongoing"
    COMPLETED = "completed"
    HIATUS = "hiatus"
    CANCELLED = "cancelled"
    DROPPED = "dropped"


class Emoji:
    CIRCLE_GREEN = "🟢"
    CIRCLE_YELLOW = "🟡"
    CIRCLE_RED = "🔴"
    CIRCLE_BROWN = "🟤"
    CHECK_GREEN = "✅"
    QUESTION_MARK = "❓"
    SQUARE_GREEN = "🟩"
    SQUARE_RED = "🟥"
    SQUARE_ORANGE = "🟧"


IgnoredTags = {
    "ddefd648-5140-4e5f-ba18-4eca4071d19b",
    "2d1f5d56-a1e5-4d0d-a961-2193588b08ec",
}
