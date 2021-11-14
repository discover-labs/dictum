from abc import ABC, abstractmethod


class DatediffCompilerMixin(ABC):
    """Mixin to calculate datediff from datepart and datetrunc implementations for
    systems that don't support datediff directly.

    The child class only needs to implement datediff_day
    """

    def datediff_year(self, args: list):
        start, end = args
        return self.datepart(["year", end]) - self.datepart(["year", start])

    def datediff_quarter(self, args: list):
        start, end = args
        return self.datediff_year(args) * 4 + (
            self.datepart(["quarter", end]) - self.datepart(["quarter", start])
        )

    def datediff_month(self, args: list):
        start, end = args
        return self.datediff_year(args) * 12 + (
            self.datepart(["month", end]) - self.datepart(["month", start])
        )

    def datediff_week(self, args: list):
        start, end = args
        start_week = self.datetrunc(["week", start])
        end_week = self.datetrunc(["week", end])
        return self.datediff_day([start_week, end_week]) / 7

    @abstractmethod
    def datediff_day(self, args: list):
        """This can't be implemented through other functions"""

    def datediff_hour(self, args: list):
        start, end = args
        days = self.datediff_day([start, end])
        return days * 24 + (
            self.datepart(["hour", end]) - self.datepart(["hour", start])
        )

    def datediff_minute(self, args: list):
        start, end = args
        hours = self.datediff_hour([start, end])
        return hours * 60 + (
            self.datepart(["minute", end]) - self.datepart(["minute", start])
        )

    def datediff_second(self, args: list):
        start, end = args
        minutes = self.datediff_minute([start, end])
        return minutes * 60 + (
            self.datepart(["second", end]) - self.datepart(["second", start])
        )

    def datediff(self, args: list):
        part, *args = args
        fn = {
            "year": self.datediff_year,
            "quarter": self.datediff_quarter,
            "month": self.datediff_month,
            "week": self.datediff_week,
            "day": self.datediff_day,
            "hour": self.datediff_hour,
            "minute": self.datediff_minute,
            "second": self.datediff_second,
        }.get(part.lower())
        if fn is None:
            raise ValueError(
                "Valid values for datediff part are year, quarter, "
                "month, week, day, hour, minute, second — "
                f"got '{part}'."
            )
        return fn(args)
