class TimeDimension:
    def __init__(cls, name, bases, attrs):
        cls.id = name
        cls.name = name
        cls.period = attrs.get("period")

    def __repr__(self):
        return self.name


class BaseTimeDimension(metaclass=TimeDimension):
    def __init__(self):
        raise ValueError("Time dimensions are singletons, don't instantiate them")


class Time(BaseTimeDimension):
    period = None


class Year(BaseTimeDimension):
    period = "year"


class Quarter(BaseTimeDimension):
    period = "quarter"


class Month(BaseTimeDimension):
    period = "month"


class Week(BaseTimeDimension):
    period = "week"


class Day(BaseTimeDimension):
    period = "day"


class Date(Day):
    period = "day"


class Hour(BaseTimeDimension):
    period = "hour"


class Minute(BaseTimeDimension):
    period = "minute"


class Second(BaseTimeDimension):
    period = "second"


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
