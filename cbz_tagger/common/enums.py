import base64

APPLICATION_MAJOR_VERSION = 4


class Urls:
    MDX = base64.b64decode("bWFuZ2FkZXgub3Jn").decode("utf-8")


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

    @classmethod
    def to_api(cls):
        return {
            "CIRCLE_GREEN": cls.CIRCLE_GREEN,
            "CIRCLE_YELLOW": cls.CIRCLE_YELLOW,
            "CIRCLE_RED": cls.CIRCLE_RED,
            "CIRCLE_BROWN": cls.CIRCLE_BROWN,
            "CHECK_GREEN": cls.CHECK_GREEN,
            "QUESTION_MARK": cls.QUESTION_MARK,
            "SQUARE_GREEN": cls.SQUARE_GREEN,
            "SQUARE_RED": cls.SQUARE_RED,
            "SQUARE_ORANGE": cls.SQUARE_ORANGE,
        }


IgnoredTags = {
    "ddefd648-5140-4e5f-ba18-4eca4071d19b",
    "2d1f5d56-a1e5-4d0d-a961-2193588b08ec",
}
