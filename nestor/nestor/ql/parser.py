from pathlib import Path

from lark import Lark, Token, Transformer

lark = Lark((Path(__file__).parent / "ql.lark").read_text(), start="query")


class Preprocessor(Transformer):
    def IDENTIFIER(self, token: Token):
        return token.value

    def STRING(self, value: str):
        return value[1:-1]  # remove enclosing '

    def INTEGER(self, value: str):
        return int(value)

    def FLOAT(self, value: str):
        return float(value)


pre = Preprocessor()


def parse_ql(query: str):
    return pre.transform(lark.parse(query))
