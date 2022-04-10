class TimeDimensionMeta:
    def __init__(cls, name, bases, attrs):
        cls.id = name
        cls.name = name
        cls.period = attrs.get("period")

    def __repr__(self):
        return self.name


class TimeDimension(metaclass=TimeDimensionMeta):
    def __init__(self):
        raise ValueError("Time dimensions are singletons, don't instantiate them")


class Time(TimeDimension):
    period = None


class Year(TimeDimension):
    period = "year"


class Quarter(TimeDimension):
    period = "quarter"


class Month(TimeDimension):
    period = "month"


class Week(TimeDimension):
    period = "week"


class Day(TimeDimension):
    period = "day"


class Date(Day):
    period = "day"


class Hour(TimeDimension):
    period = "hour"


class Minute(TimeDimension):
    period = "minute"


class Second(TimeDimension):
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
