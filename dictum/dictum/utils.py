from datetime import date, datetime

from lark import Token


def repr_expr_constant(val):
    if isinstance(val, str):
        return f"'{val}'"
    return str(val)


def value_to_token(value):
    if isinstance(value, int):
        return Token("INTEGER", str(value))
    if isinstance(value, float):
        return Token("NUMBER", str(value))
    if isinstance(value, str):
        return Token("STRING", value)
    if isinstance(value, date):
        return Token("DATE", value.strftime(r"%Y-%m-%d"))
    if isinstance(value, datetime):
        return Token("DATETIME", value.strftime(r"%Y-%m-%d %H:%M:%S"))
    raise ValueError("Token values must by integers, floats or strings")
