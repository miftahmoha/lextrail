import pytest

from lextrail.exceptions import InvalidRegex
from lextrail.regex import (
    _regex_expand_pass,
    _regex_negate_pass,
    _regex_normalize_pass,
    _regex_split_pass,
    _regex_terminalize_pass,
)


@pytest.fixture
def regex_email():
    """Regex to match email addresses."""
    return r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


def test_regex_email(regex_email: str):
    split_pass_out = _regex_split_pass(regex_email)
    assert split_pass_out == [
        "[",
        "a-z",
        "A-Z",
        "0-9",
        "_\\.\\+\\-",
        "]",
        "+",
        "@",
        "[",
        "a-z",
        "A-Z",
        "0-9",
        "\\-",
        "]",
        "+",
        "\\.",
        "[",
        "a-z",
        "A-Z",
        "0-9",
        "\\-\\.",
        "]",
        "+",
    ]

    expand_pass_out = _regex_expand_pass(split_pass_out)
    assert expand_pass_out == [
        "[",
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_\\.\\+\\-",
        "]",
        "+",
        "@",
        "[",
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\\-",
        "]",
        "+",
        "\\.",
        "[",
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\\-\\.",
        "]",
        "+",
    ]

    negate_pass_out = _regex_negate_pass(expand_pass_out)
    assert negate_pass_out == expand_pass_out

    normalize_pass_out = _regex_normalize_pass(negate_pass_out)
    # [NOTE] Rust escapes `escapable` characters inside `[]`, [\+] will only match `+`.
    assert normalize_pass_out == [
        "(",
        "a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|y|z|A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V|W|X|Y|Z|0|1|2|3|4|5|6|7|8|9|_|\\.|\\+|\\-",
        ")",
        "+",
        "@",
        "(",
        "a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|y|z|A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V|W|X|Y|Z|0|1|2|3|4|5|6|7|8|9|\\-",
        ")",
        "+",
        "\\.",
        "(",
        "a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|y|z|A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V|W|X|Y|Z|0|1|2|3|4|5|6|7|8|9|\\-|\\.",
        ")",
        "+",
    ]

    terminalize_pass_out = _regex_terminalize_pass(
        normalize_pass_out, _IS_TEST_VERSION=True
    )
    assert terminalize_pass_out == [
        "(",
        '"a"|"b"|"c"|"d"|"e"|"f"|"g"|"h"|"i"|"j"|"k"|"l"|"m"|"n"|"o"|"p"|"q"|"r"|"s"|"t"|"u"|"v"|"w"|"x"|"y"|"z"|"A"|"B"|"C"|"D"|"E"|"F"|"G"|"H"|"I"|"J"|"K"|"L"|"M"|"N"|"O"|"P"|"Q"|"R"|"S"|"T"|"U"|"V"|"W"|"X"|"Y"|"Z"|"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"|"_"|"."|"+"|"-"',
        ")",
        "+",
        '"@"',
        "(",
        '"a"|"b"|"c"|"d"|"e"|"f"|"g"|"h"|"i"|"j"|"k"|"l"|"m"|"n"|"o"|"p"|"q"|"r"|"s"|"t"|"u"|"v"|"w"|"x"|"y"|"z"|"A"|"B"|"C"|"D"|"E"|"F"|"G"|"H"|"I"|"J"|"K"|"L"|"M"|"N"|"O"|"P"|"Q"|"R"|"S"|"T"|"U"|"V"|"W"|"X"|"Y"|"Z"|"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"|"-"',
        ")",
        "+",
        '"."',
        "(",
        '"a"|"b"|"c"|"d"|"e"|"f"|"g"|"h"|"i"|"j"|"k"|"l"|"m"|"n"|"o"|"p"|"q"|"r"|"s"|"t"|"u"|"v"|"w"|"x"|"y"|"z"|"A"|"B"|"C"|"D"|"E"|"F"|"G"|"H"|"I"|"J"|"K"|"L"|"M"|"N"|"O"|"P"|"Q"|"R"|"S"|"T"|"U"|"V"|"W"|"X"|"Y"|"Z"|"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"|"-"|"."',
        ")",
        "+",
    ]


@pytest.fixture
def regex_phone_number():
    """Regex to match phone numbers in the format (123) 456-7890."""
    return r"^\(\d{3}\) \d{3}-\d{4}$"


def test_regex_phone_number(regex_phone_number: str):
    split_pass_out = _regex_split_pass(regex_phone_number)
    assert split_pass_out == [
        "\\(",
        "\\d",
        "{",
        "3",
        "}",
        "\\) ",
        "\\d",
        "{",
        "3",
        "}",
        "\\-",
        "\\d",
        "{",
        "4",
        "}",
    ]

    expand_pass_out = _regex_expand_pass(split_pass_out)
    assert expand_pass_out == [
        "\\(",
        "[",
        "0123456789",
        "]",
        "{",
        "3",
        "}",
        "\\) ",
        "[",
        "0123456789",
        "]",
        "{",
        "3",
        "}",
        "\\-",
        "[",
        "0123456789",
        "]",
        "{",
        "4",
        "}",
    ]

    negate_pass_out = _regex_negate_pass(expand_pass_out)
    assert negate_pass_out == expand_pass_out

    normalize_pass_out = _regex_normalize_pass(negate_pass_out)
    assert normalize_pass_out == [
        "\\(",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "\\) ",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "\\-",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
    ]

    terminalize_pass_out = _regex_terminalize_pass(
        normalize_pass_out, _IS_TEST_VERSION=True
    )
    assert terminalize_pass_out == [
        '"("',
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        '") "',
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        '"-"',
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
    ]


@pytest.fixture
def regex_url():
    """Regex to match URLs."""
    return r"^(https?:\/\/)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(\/[a-zA-Z0-9-._?&=]*)*$"


def test_regex_url(regex_url: str):
    split_pass_out = _regex_split_pass(regex_url)
    assert split_pass_out == [
        "(",
        "http",
        "(",
        "s",
        ")",
        "?",
        ":\\/\\/",
        ")",
        "?",
        "(",
        "[",
        "a-z",
        "A-Z",
        "0-9",
        "\\-",
        "]",
        "+",
        "\\.",
        ")",
        "+",
        "[",
        "a-z",
        "A-Z",
        "]",
        "{",
        "2,",
        "}",
        "(",
        "\\/",
        "[",
        "a-z",
        "A-Z",
        "0-9",
        "\\-\\._\\?&=",
        "]",
        "*",
        ")",
        "*",
    ]

    expand_pass_out = _regex_expand_pass(split_pass_out)
    assert expand_pass_out == [
        "(",
        "http",
        "(",
        "s",
        ")",
        "?",
        ":\\/\\/",
        ")",
        "?",
        "(",
        "[",
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\\-",
        "]",
        "+",
        "\\.",
        ")",
        "+",
        "[",
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "]",
        "{",
        "2,",
        "}",
        "(",
        "\\/",
        "[",
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\\-\\._\\?&=",
        "]",
        "*",
        ")",
        "*",
    ]

    negate_pass_out = _regex_negate_pass(expand_pass_out)
    assert negate_pass_out == expand_pass_out

    normalize_pass_out = _regex_normalize_pass(expand_pass_out)
    assert normalize_pass_out == [
        "(",
        "http",
        "(",
        "s",
        ")",
        "?",
        ":\\/\\/",
        ")",
        "?",
        "(",
        "(",
        "a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|y|z|A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V|W|X|Y|Z|0|1|2|3|4|5|6|7|8|9|\\-",
        ")",
        "+",
        "\\.",
        ")",
        "+",
        "(",
        "a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|y|z|A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V|W|X|Y|Z",
        ")",
        "(",
        "a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|y|z|A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V|W|X|Y|Z",
        ")",
        "(",
        "a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|y|z|A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V|W|X|Y|Z",
        ")",
        "*",
        "(",
        "\\/",
        "(",
        "a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|y|z|A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V|W|X|Y|Z|0|1|2|3|4|5|6|7|8|9|\\-|\\.|_|\\?|&|=",
        ")",
        "*",
        ")",
        "*",
    ]

    terminalize_pass_out = _regex_terminalize_pass(
        normalize_pass_out, _IS_TEST_VERSION=True
    )
    assert terminalize_pass_out == [
        "(",
        '"http"',
        "(",
        '"s"',
        ")",
        "?",
        '"://"',
        ")",
        "?",
        "(",
        "(",
        '"a"|"b"|"c"|"d"|"e"|"f"|"g"|"h"|"i"|"j"|"k"|"l"|"m"|"n"|"o"|"p"|"q"|"r"|"s"|"t"|"u"|"v"|"w"|"x"|"y"|"z"|"A"|"B"|"C"|"D"|"E"|"F"|"G"|"H"|"I"|"J"|"K"|"L"|"M"|"N"|"O"|"P"|"Q"|"R"|"S"|"T"|"U"|"V"|"W"|"X"|"Y"|"Z"|"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"|"-"',
        ")",
        "+",
        '"."',
        ")",
        "+",
        "(",
        '"a"|"b"|"c"|"d"|"e"|"f"|"g"|"h"|"i"|"j"|"k"|"l"|"m"|"n"|"o"|"p"|"q"|"r"|"s"|"t"|"u"|"v"|"w"|"x"|"y"|"z"|"A"|"B"|"C"|"D"|"E"|"F"|"G"|"H"|"I"|"J"|"K"|"L"|"M"|"N"|"O"|"P"|"Q"|"R"|"S"|"T"|"U"|"V"|"W"|"X"|"Y"|"Z"',
        ")",
        "(",
        '"a"|"b"|"c"|"d"|"e"|"f"|"g"|"h"|"i"|"j"|"k"|"l"|"m"|"n"|"o"|"p"|"q"|"r"|"s"|"t"|"u"|"v"|"w"|"x"|"y"|"z"|"A"|"B"|"C"|"D"|"E"|"F"|"G"|"H"|"I"|"J"|"K"|"L"|"M"|"N"|"O"|"P"|"Q"|"R"|"S"|"T"|"U"|"V"|"W"|"X"|"Y"|"Z"',
        ")",
        "(",
        '"a"|"b"|"c"|"d"|"e"|"f"|"g"|"h"|"i"|"j"|"k"|"l"|"m"|"n"|"o"|"p"|"q"|"r"|"s"|"t"|"u"|"v"|"w"|"x"|"y"|"z"|"A"|"B"|"C"|"D"|"E"|"F"|"G"|"H"|"I"|"J"|"K"|"L"|"M"|"N"|"O"|"P"|"Q"|"R"|"S"|"T"|"U"|"V"|"W"|"X"|"Y"|"Z"',
        ")",
        "*",
        "(",
        '"/"',
        "(",
        '"a"|"b"|"c"|"d"|"e"|"f"|"g"|"h"|"i"|"j"|"k"|"l"|"m"|"n"|"o"|"p"|"q"|"r"|"s"|"t"|"u"|"v"|"w"|"x"|"y"|"z"|"A"|"B"|"C"|"D"|"E"|"F"|"G"|"H"|"I"|"J"|"K"|"L"|"M"|"N"|"O"|"P"|"Q"|"R"|"S"|"T"|"U"|"V"|"W"|"X"|"Y"|"Z"|"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"|"-"|"."|"_"|"?"|"&"|"="',
        ")",
        "*",
        ")",
        "*",
    ]


@pytest.fixture
def regex_date():
    """Regex to match dates in the format YYYY-MM-DD."""
    return r"^\d{4}-\d{2}-\d{2}$"


def test_regex_date(regex_date: str):
    split_pass_out = _regex_split_pass(regex_date)
    assert split_pass_out == [
        "\\d",
        "{",
        "4",
        "}",
        "\\-",
        "\\d",
        "{",
        "2",
        "}",
        "\\-",
        "\\d",
        "{",
        "2",
        "}",
    ]

    expand_pass_out = _regex_expand_pass(split_pass_out)
    assert expand_pass_out == [
        "[",
        "0123456789",
        "]",
        "{",
        "4",
        "}",
        "\\-",
        "[",
        "0123456789",
        "]",
        "{",
        "2",
        "}",
        "\\-",
        "[",
        "0123456789",
        "]",
        "{",
        "2",
        "}",
    ]

    negate_pass_out = _regex_negate_pass(expand_pass_out)
    negate_pass_out = expand_pass_out

    normalize_pass_out = _regex_normalize_pass(negate_pass_out)
    assert normalize_pass_out == [
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "\\-",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "\\-",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
    ]

    terminalize_pass_out = _regex_terminalize_pass(
        normalize_pass_out, _IS_TEST_VERSION=True
    )
    assert terminalize_pass_out == [
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        '"-"',
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        '"-"',
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
    ]


@pytest.fixture
def regex_hex_color():
    """Regex to match hex color codes (e.g., #FFFFFF)."""
    return r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"


def test_regex_hex_color(regex_hex_color: str):
    split_pass_out = _regex_split_pass(regex_hex_color)
    assert split_pass_out == [
        "#",
        "(",
        "[",
        "A-F",
        "a-f",
        "0-9",
        "]",
        "{",
        "6",
        "}",
        "|",
        "[",
        "A-F",
        "a-f",
        "0-9",
        "]",
        "{",
        "3",
        "}",
        ")",
    ]

    expand_pass_out = _regex_expand_pass(split_pass_out)
    assert expand_pass_out == [
        "#",
        "(",
        "[",
        "ABCDEFabcdef0123456789",
        "]",
        "{",
        "6",
        "}",
        "|",
        "[",
        "ABCDEFabcdef0123456789",
        "]",
        "{",
        "3",
        "}",
        ")",
    ]

    negate_pass_out = _regex_negate_pass(expand_pass_out)
    assert negate_pass_out == expand_pass_out

    normalize_pass_out = _regex_normalize_pass(negate_pass_out)
    assert normalize_pass_out == [
        "#",
        "(",
        "(",
        "A|B|C|D|E|F|a|b|c|d|e|f|0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "A|B|C|D|E|F|a|b|c|d|e|f|0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "A|B|C|D|E|F|a|b|c|d|e|f|0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "A|B|C|D|E|F|a|b|c|d|e|f|0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "A|B|C|D|E|F|a|b|c|d|e|f|0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "A|B|C|D|E|F|a|b|c|d|e|f|0|1|2|3|4|5|6|7|8|9",
        ")",
        "|",
        "(",
        "A|B|C|D|E|F|a|b|c|d|e|f|0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "A|B|C|D|E|F|a|b|c|d|e|f|0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "A|B|C|D|E|F|a|b|c|d|e|f|0|1|2|3|4|5|6|7|8|9",
        ")",
        ")",
    ]

    terminalize_pass_out = _regex_terminalize_pass(
        normalize_pass_out, _IS_TEST_VERSION=True
    )
    assert terminalize_pass_out == [
        '"#"',
        "(",
        "(",
        '"A"|"B"|"C"|"D"|"E"|"F"|"a"|"b"|"c"|"d"|"e"|"f"|"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"A"|"B"|"C"|"D"|"E"|"F"|"a"|"b"|"c"|"d"|"e"|"f"|"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"A"|"B"|"C"|"D"|"E"|"F"|"a"|"b"|"c"|"d"|"e"|"f"|"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"A"|"B"|"C"|"D"|"E"|"F"|"a"|"b"|"c"|"d"|"e"|"f"|"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"A"|"B"|"C"|"D"|"E"|"F"|"a"|"b"|"c"|"d"|"e"|"f"|"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"A"|"B"|"C"|"D"|"E"|"F"|"a"|"b"|"c"|"d"|"e"|"f"|"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "|",
        "(",
        '"A"|"B"|"C"|"D"|"E"|"F"|"a"|"b"|"c"|"d"|"e"|"f"|"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"A"|"B"|"C"|"D"|"E"|"F"|"a"|"b"|"c"|"d"|"e"|"f"|"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"A"|"B"|"C"|"D"|"E"|"F"|"a"|"b"|"c"|"d"|"e"|"f"|"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        ")",
    ]


@pytest.fixture
def regex_username():
    """Regex to match usernames with alphanumeric characters and underscores."""
    return r"^[^a-zA-Z0-9_]{3,16}$"


def test_regex_username(regex_username: str):
    split_pass_out = _regex_split_pass(regex_username)
    assert split_pass_out == [
        "[",
        "^",
        "a-z",
        "A-Z",
        "0-9",
        "_",
        "]",
        "{",
        "3,16",
        "}",
    ]

    expand_pass_out = _regex_expand_pass(split_pass_out)
    assert expand_pass_out == [
        "[",
        "^abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
        "]",
        "{",
        "3,16",
        "}",
    ]

    negate_pass_out = _regex_negate_pass(expand_pass_out)
    assert negate_pass_out == [
        "[",
        "!\"#$%&'\\(\\)\\*\\+,\\-\\./:;<=>\\?@\\[\\\\\\]`\\{\\|\\}~ ",
        "]",
        "{",
        "3,16",
        "}",
    ]

    normalize_pass_out = _regex_normalize_pass(negate_pass_out)
    assert (
        normalize_pass_out
        == [
            "(",
            "!|\"|#|$|%|&|'|\\(|\\)|\\*|\\+|,|\\-|\\.|/|:|;|<|=|>|\\?|@|\\[|\\\\|\\]|`|\\{|\\||\\}|~| ",
            ")",
        ]
        * 3
        + [
            "(",
            "!|\"|#|$|%|&|'|\\(|\\)|\\*|\\+|,|\\-|\\.|/|:|;|<|=|>|\\?|@|\\[|\\\\|\\]|`|\\{|\\||\\}|~| ",
            ")",
            "?",
        ]
        * 16
    )

    terminalize_pass_out = _regex_terminalize_pass(
        normalize_pass_out, _IS_TEST_VERSION=True
    )
    assert (
        terminalize_pass_out
        == [
            "(",
            '"!"|"""|"#"|"$"|"%"|"&"|"\'"|"("|")"|"*"|"+"|","|"-"|"."|"/"|":"|";"|"<"|"="|">"|"?"|"@"|"["|"\\"|"]"|"`"|"{"|"|"|"}"|"~"|" "',
            ")",
        ]
        * 3
        + [
            "(",
            '"!"|"""|"#"|"$"|"%"|"&"|"\'"|"("|")"|"*"|"+"|","|"-"|"."|"/"|":"|";"|"<"|"="|">"|"?"|"@"|"["|"\\"|"]"|"`"|"{"|"|"|"}"|"~"|" "',
            ")",
            "?",
        ]
        * 16
    )


@pytest.fixture
def regex_ipv4():
    """Regex to match IPv4 addresses."""
    return r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"


def test_regex_ipv4(regex_ipv4: str):
    split_pass_out = _regex_split_pass(regex_ipv4)
    assert _regex_split_pass(regex_ipv4) == [
        "(",
        "(",
        "25",
        "[",
        "0-5",
        "]",
        "|",
        "2",
        "[",
        "0-4",
        "]",
        "[",
        "0-9",
        "]",
        "|",
        "[",
        "01",
        "]",
        "?",
        "[",
        "0-9",
        "]",
        "[",
        "0-9",
        "]",
        "?",
        ")",
        "\\.",
        ")",
        "{",
        "3",
        "}",
        "(",
        "25",
        "[",
        "0-5",
        "]",
        "|",
        "2",
        "[",
        "0-4",
        "]",
        "[",
        "0-9",
        "]",
        "|",
        "[",
        "01",
        "]",
        "?",
        "[",
        "0-9",
        "]",
        "[",
        "0-9",
        "]",
        "?",
        ")",
    ]

    expand_pass_out = _regex_expand_pass(split_pass_out)
    assert expand_pass_out == [
        "(",
        "(",
        "25",
        "[",
        "012345",
        "]",
        "|",
        "2",
        "[",
        "01234",
        "]",
        "[",
        "0123456789",
        "]",
        "|",
        "[",
        "01",
        "]",
        "?",
        "[",
        "0123456789",
        "]",
        "[",
        "0123456789",
        "]",
        "?",
        ")",
        "\\.",
        ")",
        "{",
        "3",
        "}",
        "(",
        "25",
        "[",
        "012345",
        "]",
        "|",
        "2",
        "[",
        "01234",
        "]",
        "[",
        "0123456789",
        "]",
        "|",
        "[",
        "01",
        "]",
        "?",
        "[",
        "0123456789",
        "]",
        "[",
        "0123456789",
        "]",
        "?",
        ")",
    ]

    negate_pass_out = _regex_negate_pass(expand_pass_out)
    assert negate_pass_out == expand_pass_out

    normalize_pass_out = _regex_normalize_pass(negate_pass_out)
    assert normalize_pass_out == [
        "(",
        "(",
        "25",
        "(",
        "0|1|2|3|4|5",
        ")",
        "|",
        "2",
        "(",
        "0|1|2|3|4",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "|",
        "(",
        "0|1",
        ")",
        "?",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "?",
        ")",
        "\\.",
        ")",
        "(",
        "(",
        "25",
        "(",
        "0|1|2|3|4|5",
        ")",
        "|",
        "2",
        "(",
        "0|1|2|3|4",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "|",
        "(",
        "0|1",
        ")",
        "?",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "?",
        ")",
        "\\.",
        ")",
        "(",
        "(",
        "25",
        "(",
        "0|1|2|3|4|5",
        ")",
        "|",
        "2",
        "(",
        "0|1|2|3|4",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "|",
        "(",
        "0|1",
        ")",
        "?",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "?",
        ")",
        "\\.",
        ")",
        "(",
        "25",
        "(",
        "0|1|2|3|4|5",
        ")",
        "|",
        "2",
        "(",
        "0|1|2|3|4",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "|",
        "(",
        "0|1",
        ")",
        "?",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "(",
        "0|1|2|3|4|5|6|7|8|9",
        ")",
        "?",
        ")",
    ]

    terminalize_pass_out = _regex_terminalize_pass(
        normalize_pass_out, _IS_TEST_VERSION=True
    )
    assert terminalize_pass_out == [
        "(",
        "(",
        '"25"',
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"',
        ")",
        "|",
        '"2"',
        "(",
        '"0"|"1"|"2"|"3"|"4"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "|",
        "(",
        '"0"|"1"',
        ")",
        "?",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "?",
        ")",
        '"."',
        ")",
        "(",
        "(",
        '"25"',
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"',
        ")",
        "|",
        '"2"',
        "(",
        '"0"|"1"|"2"|"3"|"4"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "|",
        "(",
        '"0"|"1"',
        ")",
        "?",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "?",
        ")",
        '"."',
        ")",
        "(",
        "(",
        '"25"',
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"',
        ")",
        "|",
        '"2"',
        "(",
        '"0"|"1"|"2"|"3"|"4"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "|",
        "(",
        '"0"|"1"',
        ")",
        "?",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "?",
        ")",
        '"."',
        ")",
        "(",
        '"25"',
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"',
        ")",
        "|",
        '"2"',
        "(",
        '"0"|"1"|"2"|"3"|"4"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "|",
        "(",
        '"0"|"1"',
        ")",
        "?",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "(",
        '"0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"',
        ")",
        "?",
        ")",
    ]


@pytest.fixture
def regex_html_tag():
    """Regex to match simple HTML tags."""
    return r"^<([a-z]+)([^<]+)*(?:>(.*)<\/\1)>|\s+\/>)$"


def test_regex_html_tag_unsupported(regex_html_tag: str):
    with pytest.raises(InvalidRegex) as exc_info:
        _regex_split_pass(regex_html_tag)

    assert str(exc_info.value) == "Backreferences are not supported yet."


@pytest.fixture
def regex_mixed_unicode_and_special_characters():
    return r"[\u00A0-\uFFFF\w\d\s]{2,}|[^\x00-\x7F]+"


def test_regex_mixed_unicode_and_special_characters_unsupported(
    regex_mixed_unicode_and_special_characters: str,
):
    with pytest.raises(InvalidRegex) as exc_info:
        _regex_split_pass(regex_mixed_unicode_and_special_characters)

    assert str(exc_info.value) == "Unicode characters are not supported yet."


@pytest.fixture
def regex_extreme_quantifiers_and_escaped_metacharacters():
    return r"(\.\*\?\+\\|[\{\}\[\]\(\)]){,10}"


def test_regex_extreme_quantifiers_and_escaped_metacharacters(
    regex_extreme_quantifiers_and_escaped_metacharacters: str,
):
    split_pass_out = _regex_split_pass(
        regex_extreme_quantifiers_and_escaped_metacharacters
    )
    assert split_pass_out == [
        "(",
        "\\.\\*\\?\\+\\\\",
        "|",
        "[",
        "\\{\\}\\[\\]\\(\\)",
        "]",
        ")",
        "{",
        ",10",
        "}",
    ]

    expand_pass_out = _regex_expand_pass(split_pass_out)
    assert expand_pass_out == split_pass_out

    negate_pass_out = _regex_negate_pass(expand_pass_out)
    assert negate_pass_out == expand_pass_out

    normalize_pass_out = _regex_normalize_pass(negate_pass_out)
    assert (
        normalize_pass_out
        == [
            "(",
            "\\.\\*\\?\\+\\\\",
            "|",
            "(",
            "\\{|\\}|\\[|\\]|\\(|\\)",
            ")",
            ")",
            "?",
        ]
        * 10
    )

    terminalize_pass_out = _regex_terminalize_pass(
        normalize_pass_out, _IS_TEST_VERSION=True
    )
    assert (
        terminalize_pass_out
        == [
            "(",
            '".*?+\\"',
            "|",
            "(",
            '"{"|"}"|"["|"]"|"("|")"',
            ")",
            ")",
            "?",
        ]
        * 10
    )
