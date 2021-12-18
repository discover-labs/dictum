from functools import cache
from typing import Optional

from babel.core import Locale

from dictum.project.altair.format import (
    ldml_date_to_d3_time_format,
    ldml_number_to_d3_format,
)

currency_symbol_overrides = {
    "RUB": "₽",
    None: "",
}


def get_default_format_for_kind(kind: str, locale: str) -> str:
    data = load_locale(locale)
    if kind == "date":
        return ldml_date_to_d3_time_format(data.date_formats["short"].pattern)
    if kind == "datetime":
        short_date = data.date_formats["short"].pattern
        short_time = data.time_formats["short"].pattern
        datetime = data.datetime_formats["short"].format(short_time, short_date)
        return ldml_date_to_d3_time_format(datetime)
    if kind == "currency":
        return ldml_number_to_d3_format(data.currency_formats["standard"].pattern)
    if kind == "percent":
        return ldml_number_to_d3_format(data.percent_formats[None].pattern)
    if kind in {"number", "decimal"}:
        return ldml_number_to_d3_format(data.decimal_formats[None].pattern)


@cache
def load_locale(locale: str) -> Locale:
    return Locale(locale)


def cldr_locale_to_d3_number(locale: str, currency: Optional[str] = None):
    data = load_locale(locale)
    fix, start = "", True
    if currency is not None:
        symbol = currency_symbol_overrides.get(currency)
        if symbol is None:
            symbol = data.currency_symbols.get(currency, currency)
        fmt = data.currency_formats["standard"]
        start = fmt.pattern.startswith("¤")
        fix = fmt.prefix[0] if start else fmt.suffix[0]
        fix = fix.replace("¤", symbol)
    return {
        "decimal": data.number_symbols["decimal"],
        "thousands": data.number_symbols["group"],
        "grouping": list(next(iter(data.decimal_formats.values())).grouping),
        "currency": [fix, ""] if start else ["", fix],
    }


def cldr_locale_to_d3_time(locale: str):
    data = load_locale(locale)
    days = [6] + list(range(6))  # days in d3 start from Sunday
    short_date = ldml_date_to_d3_time_format(data.date_formats["short"].pattern)
    short_time = ldml_date_to_d3_time_format(data.time_formats["short"].pattern)
    datetime = data.datetime_formats["short"].format(short_time, short_date)
    return {
        "dateTime": datetime,
        "date": short_date,
        "time": short_time,
        "periods": [
            data.day_periods["format"]["abbreviated"]["am"],
            data.day_periods["format"]["abbreviated"]["pm"],
        ],
        "days": [data.days["format"]["wide"][k] for k in days],
        "shortDays": [data.days["format"]["abbreviated"][k] for k in days],
        "months": [data.months["format"]["wide"][k] for k in range(1, 13)],
        "shortMonths": [data.months["format"]["abbreviated"][k] for k in range(1, 13)],
    }


def cldr_locale_to_d3(locale: str, currency: Optional[str] = None):
    return {
        "number": cldr_locale_to_d3_number(locale, currency=currency),
        "time": cldr_locale_to_d3_time(locale),
    }
