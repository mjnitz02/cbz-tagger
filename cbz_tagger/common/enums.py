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
    MDX = "mangadex.org"
    MSE = "mangasee123.com"
    CMK = "api.comick.fun"
    WBC = "weebcentral.com"


class Plugins:
    MDX = "mdx"
    MSE = "mse"
    CMK = "cmk"
    WBC = "wbc"

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
