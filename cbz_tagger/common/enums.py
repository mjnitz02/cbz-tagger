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
    MSE = base64.b64decode("bWFuZ2FzZWUxMjMuY29t").decode("utf-8")
    CMK = base64.b64decode("YXBpLmNvbWljay5mdW4=").decode("utf-8")
    WBC = base64.b64decode("d2VlYmNlbnRyYWwuY29t").decode("utf-8")


class Plugins:
    MDX = "mdx"
    MSE = "mse"
    CMK = "cmk"
    WBC = "wbc"

    TITLE_URLS = {
        MDX: f"https://{Urls.MDX}/title/",
        MSE: f"https://{Urls.MSE}/manga/",
        CMK: f"https://{Urls.CMK}/comic/",
        WBC: f"https://{Urls.WBC}/series/",
    }

    @classmethod
    def all(cls):
        return [cls.MDX, cls.MSE, cls.CMK, cls.WBC]


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
