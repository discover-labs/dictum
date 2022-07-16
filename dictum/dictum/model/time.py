from dictum.schema import FormatConfig


class TimeDimension:
    def __init__(cls, name, bases, attrs):
        cls.id = name
        cls.name = name
        cls.period = attrs.get("period")
        cls.pattern = attrs.get("pattern")
        cls.skeleton = attrs.get("skeleton")

    def __repr__(self):
        return self.name

    @property
    def format(self) -> FormatConfig:
        if self.skeleton:
            return FormatConfig(kind="datetime", skeleton=self.skeleton)
        if self.pattern:
            return FormatConfig(kind="datetime", pattern=self.pattern)
        raise ValueError  # this shouldn't happen


class BaseTimeDimension(metaclass=TimeDimension):
    pattern: str = None
    skeleton: str = None

    def __init__(self):
        raise ValueError("Time dimensions are singletons, don't instantiate them")


class Time(BaseTimeDimension):
    period = None
    skeleton = "yyMMdHmmss"


class Year(BaseTimeDimension):
    period = "year"
    pattern = "yy"


class Quarter(BaseTimeDimension):
    period = "quarter"
    pattern = "qqqq yy"


class Month(BaseTimeDimension):
    period = "month"
    skeleton = "MMMMy"


class Week(BaseTimeDimension):
    period = "week"
    skeleton = "w Y"


class Day(BaseTimeDimension):
    period = "day"
    skeleton = "yMd"


class Date(Day):
    period = "day"


class Hour(BaseTimeDimension):
    period = "hour"
    skeleton = "yMd hh"


class Minute(BaseTimeDimension):
    period = "minute"
    skeleton = "yMd hm"


class Second(BaseTimeDimension):
    period = "second"
    skeleton = "yMd hms"


dimensions = {
    "Time": Time,
    "Year": Year,
    "Quarter": Quarter,
    "Month": Month,
    "Week": Week,
    "Day": Day,
    "Date": Date,
    "Hour": Hour,
    "Minute": Minute,
    "Second": Second,
}
