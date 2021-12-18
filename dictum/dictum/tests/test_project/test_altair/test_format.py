from dictum.project.altair.format import ldml_number_to_d3_format


def test_sign():
    assert ldml_number_to_d3_format("#") == "d"
    assert ldml_number_to_d3_format("+#") == "+d"
    assert ldml_number_to_d3_format("#;(#)") == "(d"
    assert ldml_number_to_d3_format(" #;-#") == " d"


def test_symbol():
    assert ldml_number_to_d3_format("¤#") == "$d"
    assert ldml_number_to_d3_format("#¤") == "$d"


def test_zero():
    assert ldml_number_to_d3_format("0000") == "04d"
    assert ldml_number_to_d3_format("#,#00") == "02,d"


def test_width():
    assert ldml_number_to_d3_format("00") == "02d"


def test_comma():
    assert ldml_number_to_d3_format("###") == "d"
    assert ldml_number_to_d3_format("#,###") == ",d"
    assert ldml_number_to_d3_format(",##") == ",d"
    assert ldml_number_to_d3_format("#,##,###") == ",d"


def test_precision():
    assert ldml_number_to_d3_format("#.##") == ".2~f"
    assert ldml_number_to_d3_format("#.00") == ".2f"

    # this can't be represented with d3-format
    # we choose between keeping precision (rounding)
    # instead of enforcing zero-padding and having to round to 2
    assert ldml_number_to_d3_format("#.00##") == ".4~f"


def test_type():
    assert ldml_number_to_d3_format("#%") == ".0%"

    # d3-format doesn't support % as prefix, same as #%
    assert ldml_number_to_d3_format("%#") == ".0%"

    assert ldml_number_to_d3_format("#.##E#") == ".2~e"
    assert ldml_number_to_d3_format("#.00E#") == ".2e"

    # in this case babel doesn't format the number as scientific
    # without # or 0 after E, so this is correct
    assert ldml_number_to_d3_format("#.##E") == ".2~f"

    assert ldml_number_to_d3_format("#.") == "d"

    assert ldml_number_to_d3_format("@@@") == ".3r"

    # same as with precision, this can't be represented
    # and we opt for keeping the rounding instead of padding
    assert ldml_number_to_d3_format("@@@##") == ".5~r"
