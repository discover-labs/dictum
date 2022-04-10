from typing import Dict, List, Optional

from babel.dates import format_date, format_datetime
from babel.numbers import format_currency, format_decimal, format_percent

from dictum import schema


class Formatter:
    """Intelligently format the data based on the information in the query."""

    formatters = {
        "number": format_decimal,
        "decimal": format_decimal,
        "percent": format_percent,
        "date": format_date,
        "datetime": format_datetime,
    }

    def __init__(
        self,
        locale: str,
        formats: Dict[str, schema.FormatConfig],
    ):
        self.locale = locale
        self.formats = formats

    def format(self, data: List[dict]):
        for row in data:
            yield self.format_row(row)

    def format_row(self, row: dict):
        return {k: self.format_value(v, self.formats[k]) for k, v in row.items()}

    def format_value(self, value, format: schema.FormatConfig) -> Optional[str]:
        if value is None:
            return None
        if format.kind == "string":
            return str(value)
        if format.kind == "currency":
            return format_currency(
                value, format.currency, format=format.pattern, locale=self.locale
            )
        formatter = self.formatters[format.kind]
        return formatter(value, format=format.pattern, locale=self.locale)
