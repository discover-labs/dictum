from collections import UserDict

from dictum.model.calculations import Calculation, Dimension, Measure, Metric


class CalculationDict(UserDict):
    def __getitem__(self, key: str):
        result = self.data.get(key)
        if result is None:
            raise KeyError(f"{self.T.__name__} {key} does not exist")
        return result

    def __setitem__(self, name: str, value):
        if name in self.data:
            raise KeyError(
                f"Duplicate {self.T.__name__.lower()}: {name} on tables "
                f"{self.get(name).table.id} and {value.table.id}"
            )
        return super().__setitem__(name, value)

    def get(self, key: str):
        return self[key]

    def add(self, calc: "Calculation"):
        self[calc.id] = calc


class MeasureDict(CalculationDict):
    T = Measure

    def get(self, key: str) -> Measure:
        return super().get(key)


class DimensionDict(CalculationDict):
    T = Dimension

    def get(self, key: str) -> Dimension:
        return super().get(key)


class MetricDict(CalculationDict):
    T = Metric

    def get(self, key: str) -> Metric:
        return super().get(key)
