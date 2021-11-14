from pathlib import Path

from lark import Lark, Token, Transformer

lark = Lark((Path(__file__).parent / "ql.lark").read_text(), start="query")


class Preprocessor(Transformer):
    def identifier(self, children: list):
        return children[0]

    def IDENTIFIER(self, token: Token):
        return token.value

    def QUOTED_IDENTIFIER(self, token: Token):
        return token.value[1:-1]  # unquote

    def STRING(self, value: str):
        return value[1:-1]  # unquote

    def INTEGER(self, value: str):
        return int(value)

    def FLOAT(self, value: str):
        return float(value)


pre = Preprocessor()


def parse_ql(query: str):
    return pre.transform(lark.parse(query))
