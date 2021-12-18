import pytest
from babel.localedata import locale_identifiers

from dictum.project.altair.locale import (
    cldr_locale_to_d3_number,
    cldr_locale_to_d3_time,
)


def test_d3_en_US_locale_number():
    assert cldr_locale_to_d3_number("en_US") == {
        "decimal": ".",
        "thousands": ",",
        "grouping": [3, 3],
        "currency": ["", ""],
    }
    assert cldr_locale_to_d3_number("en_US", "USD") == {
        "decimal": ".",
        "thousands": ",",
        "grouping": [3, 3],
        "currency": ["$", ""],
    }


def test_d3_en_RU_locale_number():
    """Just a familiar alternative locale"""
    assert cldr_locale_to_d3_number("ru_RU") == {
        "decimal": ",",
        "thousands": "\xa0",
        "grouping": [3, 3],
        "currency": ["", ""],
    }
    assert cldr_locale_to_d3_number("ru_RU", "RUB") == {
        "decimal": ",",
        "thousands": "\xa0",
        "grouping": [3, 3],
        "currency": ["", "\xa0₽"],
    }


locales = locale_identifiers()


@pytest.mark.parametrize("locale", locales)
def test_number_locales(locale: str):
    """Test that all number locales build"""
    cldr_locale_to_d3_number(locale, "USD")
    cldr_locale_to_d3_number(locale, "CNY")
    cldr_locale_to_d3_number(locale, "RUB")
    cldr_locale_to_d3_number(locale, "UAH")


@pytest.mark.parametrize("locale", locales)
def test_d3_en_US_locale_time(locale: str):
    cldr_locale_to_d3_time(locale)
