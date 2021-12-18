class ArithmeticCompilerMixin:
    def FLOAT(self, value: str):
        return float(value)

    def INTEGER(self, value: str):
        return int(value)

    def STRING(self, value: str):
        return value

    def TRUE(self):
        return True

    def FALSE(self):
        return False

    def exp(self, a, b):
        return a ** b

    def neg(self, value):
        return -value

    def div(self, a, b):
        return a / b

    def mul(sef, a, b):
        return a * b

    def mod(self, a, b):
        return a % b

    def add(self, a, b):
        return a + b

    def sub(self, a, b):
        return a - b

    def gt(self, a, b):
        return a > b

    def ge(self, a, b):
        return a >= b

    def lt(self, a, b):
        return a < b

    def le(self, a, b):
        return a <= b

    def eq(self, a, b):
        return a == b

    def ne(self, a, b):
        return a != b

    def IN(self, value, values):
        return value in values

    def NOT(self, value):
        return not value

    def AND(self, a, b):
        return a and b

    def OR(self, a, b):
        return a or b
