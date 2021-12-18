from babel import dates, numbers


def ldml_number_to_d3_format(pattern: str) -> str:
    """Convert CLDR number format pattern to d3-format specifier.

    Since CLDR only supports zero padding, fill and align aren't used.
    See tests for comments on what can't be supported.

    [[fill]align][sign][symbol][0][width][,][.precision][~][type]

    e - exponent notation.
    f - fixed point notation.
    g - either decimal or exponent notation, rounded to significant digits.
    r - decimal notation, rounded to significant digits.
    s - decimal notation with an SI prefix, rounded to significant digits.
    % - multiply by 100, and then decimal notation with a percent sign.
    p - multiply by 100, round to significant digits, and then decimal notation with a
        percent sign.
    b - binary notation, rounded to integer.
    o - octal notation, rounded to integer.
    d - decimal notation, rounded to integer.
    x - hexadecimal notation, using lower-case letters, rounded to integer.
    X - hexadecimal notation, using upper-case letters, rounded to integer.
    c - character data, for a string of text.
    """
    pat: numbers.NumberPattern = numbers.parse_pattern(pattern)

    sign = ""
    if pat.prefix[0] == "+":
        sign = "+"
    elif pat.prefix[0] == " ":
        sign = " "
    elif pat.prefix[1] == "(":
        sign = "("

    symbol = ""
    if "¤" in "".join(pat.prefix + pat.suffix):
        symbol = "$"

    zero = ""
    if pat.int_prec[0] > 0:
        zero = "0"

    width = ""
    if pat.int_prec[0] > 0:
        width = f"{pat.int_prec[0]}"

    comma = ""
    if pat.grouping != (1000, 1000):  # that's how no grouping is reprd in babel
        comma = ","

    tilde = ""
    if pat.frac_prec[0] != pat.frac_prec[1]:
        tilde = "~"

    precision = max(pat.frac_prec)

    type_ = ""
    if "%" in "".join(pat.suffix + pat.prefix) and pat.scale == 2:
        type_ = "%"
    elif pat.exp_prec is not None:
        type_ = "e"
    elif "@" in pattern:
        # precision doesn't mean the same thing for r type
        if pat.int_prec[0] != pat.int_prec[1]:
            tilde = "~"
        precision = pat.int_prec[1]
        zero, width = "", ""
        type_ = "r"
    elif precision == 0:
        type_ = "d"
    else:
        type_ = "f"

    precision = f".{precision}"

    if type_ == "d":
        precision = ""

    return f"{sign}{symbol}{zero}{width}{comma}{precision}{tilde}{type_}"


class DateFormatMapper:
    mapping = {
        # Year
        "Y": "%-y",
        "YY": "%y",
        "YYYY": "%Y",
        "y": "%-Y",
        "yyyy": "%G",
        "yy": "%g",
        # Quarter
        "Q": "%-q",
        "QQ": "%q",
        "QQQ": "%q",
        "q": "%-q",
        "qq": "%q",
        "qqq": "%q",
        # Month
        "M": "%-m",
        "MM": "%m",
        "MMM": "%b",
        "MMMM": "%B",
        "MMMMM": "%b",
        "L": "%-m",
        "LL": "%m",
        "LLL": "%b",
        "LLLL": "%B",
        "LLLLL": "%b",
        # Week
        "w": "%-V",
        "ww": "%V",
        "W": "%-W",
        "WW": "%W",
        # Day
        "d": "%-d",
        "dd": "%d",
        "D": "%-j",
        "DD": "%j",
        "DDD": "%j",
        # lala
        "E": "%a",  # abbreviated
        "EE": "%a",
        "EEE": "%a",
        "EEEE": "%A",  # full
        "EEEEE": "%a",  # narrow
        # month name
        "MMM": "%b",
        "MMMM": "%B",
        "MMMMM": "%b",
        "LLL": "%b",
        "LLLL": "%B",
        "LLLLL": "%b",
        # day of month
        "d": "%-d",
        "dd": "%d",
        "D": "%-j",
        "DD": "%j",
        "DDD": "%j",
        # day of week
        "E": "%a",
        "EE": "%a",
        "EEE": "%a",
        "EEEE": "%A",
        "e": "%a",
        "ee": "%a",
        "eee": "%a",
        "eeee": "%A",
        # Time period (AM/PM)
        "a": "%p",
        # Hour
        "h": "%-I",
        "hh": "%I",
        "H": "%-H",
        "HH": "%H",
        "K": "%-I",
        "KK": "%I",
        "k": "%-H",
        "kk": "%H",
        # Minute
        "m": "%-m",
        "mm": "%m",
        # Second
        "s": "%-S",
        "ss": "%S",
        "S": "%-S",
        "SS": "%S",
        # Timezone
        "z": "%Z",
        "zz": "%Z",
        "zzz": "%Z",
        "zzzz": "%Z",
        "Z": "%Z",
        "ZZ": "%Z",
        "ZZZ": "%Z",
        "ZZZZ": "%Z",
    }

    def __getitem__(self, key: str):
        return self.mapping.get(key, "")


mapper = DateFormatMapper()


def ldml_date_to_d3_time_format(pattern: str) -> str:
    pat = dates.parse_pattern(pattern)
    return pat.format % mapper
