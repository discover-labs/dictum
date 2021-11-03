from datetime import date, datetime
from numbers import Number
from typing import Dict, List, Optional

from babel.dates import format_date, format_datetime
from babel.numbers import format_currency, format_decimal, format_number, format_percent

from nestor.store.calculations import Calculation


class Formatter:
    """Intelligently format the data based on the information in the query."""

    def __init__(
        self,
        locale: str,
        fields: Dict[str, Calculation],
        formatting: bool = True,
    ):
        self.locale = locale
        self.fields = fields
        self.formatting = formatting

    def format(self, data: List[dict]):
        if not self.formatting:
            yield from self.format_no_formatting(data)
        else:
            for row in data:
                yield self.format_row(row)

    def format_no_formatting(self, data: List[dict]):
        for row in data:
            yield self.format_row_no_formatting(row)

    def format_row_no_formatting(self, row: dict):
        result = row.copy()
        for column, value in result.items():
            if self.fields[column].type == "date":
                result[column] = self.date(value, format="yyyy-MM-dd")
            elif self.fields[column].type == "datetime":
                result[column] = self.datetime(value, format="yyyy-MM-dd HH:MM:SS")
        return result

    def format_row(self, row: dict):
        for k, v in row.items():
            field = self.fields[k]
            row[k] = self.format_type(
                row[k], type=field.type, format=field.format, currency=field.currency
            )
        return row

    def format_type(
        self,
        value,
        type: str,
        format: Optional[str] = None,
        currency: Optional[str] = None,
    ):
        if type == "currency":
            return self.currency(value=value, currency=currency, format=format)
        return getattr(self, type)(value, format=format)

    def number(self, value: Number, format: Optional[str] = None) -> str:
        if format is not None:
            return self.decimal(value, format)
        return format_number(value, locale=self.locale)

    def decimal(self, value: Number, format: Optional[str] = None) -> str:
        if format is not None:
            return format_decimal(value, format=format, locale=self.locale)
        return format_decimal(value, locale=self.locale)

    def percent(self, value: Number, format: Optional[str] = None) -> str:
        if format is not None:
            return format_percent(value, format=format, locale=self.locale)
        return format_percent(value, locale=self.locale)

    def currency(
        self, value: Number, currency: str, format: Optional[str] = None
    ) -> str:
        if format is not None:
            return format_currency(
                value, currency=currency, format=format, locale=self.locale
            )
        return format_currency(value, currency=currency, locale=self.locale)

    def date(self, value: date, format: Optional[str] = None) -> str:
        if format is not None:
            return format_date(value, format=format, locale=self.locale)
        return format_date(value, locale=self.locale)

    def datetime(self, value: datetime, format: Optional[str] = None) -> str:
        if format is not None:
            return format_datetime(value, format=format, locale=self.locale)
        return format_datetime(value, locale=self.locale)

    def string(self, value, format: Optional[str] = None):
        return str(value)
