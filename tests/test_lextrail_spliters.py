import pytest

from lextrail.build.passes import _split_symbols
from lextrail.guide.passes import (
    _split_cfg_grammar,
    _divide_cfg_grammar_into_rules,
)
from lextrail.regex import _regex_split_pass, _regex_expand_pass, _regex_negate_pass
from lextrail.exceptions import InvalidRegex


@pytest.fixture
def def_with_out_or_without_special_delimiters():
    return """ "(" expression ( (factor "-") |  /[0-9]*.[0-9]*/) ")" """


def test_split_symbols_with_out_or_without_special_delimiters(
    def_with_out_or_without_special_delimiters: str,
):
    result = _split_symbols(def_with_out_or_without_special_delimiters)

    assert result == _split_symbols(
        def_with_out_or_without_special_delimiters.replace(" ", "")
    )
    assert result == [
        '"("',
        "expression",
        "(",
        "(",
        "factor",
        '"-"',
        ")",
        "|",
        "/[0-9]*.[0-9]*/",
        ")",
        '")"',
    ]


@pytest.fixture
def def_with_in_and_out_or_with_special_delimiters_once_any():
    return """ "(" expression ((factor "-")+ | </[0-9]*.[0-9]*/ | "+">) ")" """


def test_split_symbols_with_in_and_out_or_with_special_delimiters_once_any(
    def_with_in_and_out_or_with_special_delimiters_once_any: str,
):
    result = _split_symbols(def_with_in_and_out_or_with_special_delimiters_once_any)

    assert result == _split_symbols(
        def_with_in_and_out_or_with_special_delimiters_once_any.replace(" ", "")
    )
    assert result == [
        '"("',
        "expression",
        "(",
        "<",
        "factor",
        '"-"',
        ">",
        "|",
        "<",
        "/[0-9]*.[0-9]*/",
        "|",
        '"+"',
        ">",
        ")",
        '")"',
    ]


@pytest.fixture
def def_with_in_and_out_ext_or_seq_with_special_delimiters_none_any():
    return """ "(" expression {(factor "-") ("+" power) | {/[0-9]*.[0-9]*/ factor | "+" expression}} ")" """


def test_split_symbols_with_in_and_out_ext_or_seq_with_special_delimiters_none_any(
    def_with_in_and_out_ext_or_seq_with_special_delimiters_none_any: str,
):
    result = _split_symbols(
        def_with_in_and_out_ext_or_seq_with_special_delimiters_none_any
    )
    assert result == _split_symbols(
        def_with_in_and_out_ext_or_seq_with_special_delimiters_none_any.replace(" ", "")
    )
    assert result == [
        '"("',
        "expression",
        "{",
        "(",
        "factor",
        '"-"',
        ")",
        "(",
        '"+"',
        "power",
        ")",
        "|",
        "{",
        "/[0-9]*.[0-9]*/",
        "factor",
        "|",
        '"+"',
        "expression",
        "}",
        "}",
        '")"',
    ]


@pytest.fixture
def def_with_in_and_out_ext_or_seq_with_special_delimiters_none_once():
    return """ "(" expression [(factor "-") ("+" power) | [/[0-9]*.[0-9]*/ factor | "+" expression]] ")" """


def test_split_symbols_with_in_and_out_ext_or_seq_with_special_delimiters_none_once(
    def_with_in_and_out_ext_or_seq_with_special_delimiters_none_once: str,
):
    result = _split_symbols(
        def_with_in_and_out_ext_or_seq_with_special_delimiters_none_once
    )

    assert result == _split_symbols(
        def_with_in_and_out_ext_or_seq_with_special_delimiters_none_once.replace(
            " ", ""
        )
    )
    assert result == [
        '"("',
        "expression",
        "[",
        "(",
        "factor",
        '"-"',
        ")",
        "(",
        '"+"',
        "power",
        ")",
        "|",
        "[",
        "/[0-9]*.[0-9]*/",
        "factor",
        "|",
        '"+"',
        "expression",
        "]",
        "]",
        '")"',
    ]


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_once_any_none_once():
    return """ "(" expression {<factor "-"> ("/" factor) ["+" power] expression (/[0-9]*.[0-9]*/ "*") | [/[0-9]*.[0-9]*/ factor | "+" expression]} ")" """


def test_split_symbols_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_once_any_none_once(
    def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_once_any_none_once: str,
):
    result = _split_symbols(
        def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_once_any_none_once
    )

    assert result == _split_symbols(
        def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_once_any_none_once.replace(
            " ", ""
        )
    )
    assert result == [
        '"("',
        "expression",
        "{",
        "<",
        "factor",
        '"-"',
        ">",
        "(",
        '"/"',
        "factor",
        ")",
        "[",
        '"+"',
        "power",
        "]",
        "expression",
        "(",
        "/[0-9]*.[0-9]*/",
        '"*"',
        ")",
        "|",
        "[",
        "/[0-9]*.[0-9]*/",
        "factor",
        "|",
        '"+"',
        "expression",
        "]",
        "}",
        '")"',
    ]


@pytest.fixture
def cfg_without_escapes():
    return """
    start: expression

    expression: (term (("+" | "-") term)) | "^" expression

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """


def test_split_cfg_grammar_without_escapes(
    cfg_without_escapes: str,
):
    lines = [line.strip() for line in _split_cfg_grammar(cfg_without_escapes)]

    assert lines == [
        "start: expression",
        'expression: (term (("+" | "-") term)) | "^" expression',
        'term: factor (("*" | "/") factor)',
        "factor: NUMBER",
        "NUMBER: /-?[0-9]+/",
    ]


def test_divide_cfg_grammar_into_rules_without_escapes(
    cfg_without_escapes: str,
):
    rules: dict[str, str] = _divide_cfg_grammar_into_rules(cfg_without_escapes)

    assert rules == {
        "start": "expression",
        "expression": '(term (("+" | "-") term)) | "^" expression',
        "term": 'factor (("*" | "/") factor)',
        "factor": "NUMBER",
        "NUMBER": "/-?[0-9]+/",
    }


@pytest.fixture
def cfg_with_escapes():
    return """
    start: expression

    expression: (term (("+" | "\n") term)) | "^" expression

    term: factor (("*" | "\t") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """


def test_split_cfg_grammar_with_escapes(
    cfg_with_escapes: str,
):
    lines = [line.strip() for line in _split_cfg_grammar(cfg_with_escapes)]

    assert lines == [
        "start: expression",
        'expression: (term (("+" | "\n") term)) | "^" expression',
        'term: factor (("*" | "\t") factor)',
        "factor: NUMBER",
        "NUMBER: /-?[0-9]+/",
    ]


def test_divide_cfg_grammar_into_rules_with_escapes(
    cfg_with_escapes: str,
):
    rules: dict[str, str] = _divide_cfg_grammar_into_rules(cfg_with_escapes)

    assert rules == {
        "start": "expression",
        "expression": '(term (("+" | "\n") term)) | "^" expression',
        "term": 'factor (("*" | "\t") factor)',
        "factor": "NUMBER",
        "NUMBER": "/-?[0-9]+/",
    }


@pytest.fixture
def cfg_with_multlines():
    return """
    start: expression

    expression: (term (("+" | "\n") term)) 
    | "^" expression

    term: factor (("*" | "\t") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """


def test_split_cfg_grammar_with_multlines(
    cfg_with_multlines: str,
):
    lines = [line.strip() for line in _split_cfg_grammar(cfg_with_multlines)]

    assert lines == [
        "start: expression",
        'expression: (term (("+" | "\n") term))',
        '| "^" expression',
        'term: factor (("*" | "\t") factor)',
        "factor: NUMBER",
        "NUMBER: /-?[0-9]+/",
    ]


def test_divide_cfg_grammar_into_rules_with_multlines(
    cfg_with_multlines: str,
):
    rules: dict[str, str] = _divide_cfg_grammar_into_rules(cfg_with_multlines)

    assert rules == {
        "start": "expression",
        "expression": '(term (("+" | "\n") term)) | "^" expression',
        "term": 'factor (("*" | "\t") factor)',
        "factor": "NUMBER",
        "NUMBER": "/-?[0-9]+/",
    }


@pytest.fixture
def regex_email():
    """Regex to match email addresses."""
    return r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


def test_regex_email_split_pass(regex_email: str):
    assert _regex_split_pass(regex_email) == [
        "[",
        "a-z",
        "A-Z",
        "0-9",
        "_\\.\\+-",
        "]",
        "+",
        "@",
        "[",
        "a-z",
        "A-Z",
        "0-9",
        "-",
        "]",
        "+",
        "\\.",
        "[",
        "a-z",
        "A-Z",
        "0-9",
        "-\\.",
        "]",
        "+",
    ]


@pytest.fixture
def regex_phone_number():
    """Regex to match phone numbers in the format (123) 456-7890."""
    return r"^\(\d{3}\) \d{3}-\d{4}$"


def test_regex_phone_number_split_pass(regex_phone_number: str):
    assert _regex_split_pass(regex_phone_number) == [
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
        "-",
        "\\d",
        "{",
        "4",
        "}",
    ]


# [TODO] Add error if `/` is not escaped in main parsing unit.
@pytest.fixture
def regex_url():
    """Regex to match URLs."""
    return r"^(https?:\/\/)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(\/[a-zA-Z0-9-._?&=]*)*$"


def test_regex_url_split_pass(regex_url: str):
    assert _regex_split_pass(regex_url) == [
        "(",
        "https",
        "?",
        ":\\/\\/",
        ")",
        "?",
        "(",
        "[",
        "a-z",
        "A-Z",
        "0-9",
        "-",
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
        "-\\._\\?&=",
        "]",
        "*",
        ")",
        "*",
    ]


@pytest.fixture
def regex_date():
    """Regex to match dates in the format YYYY-MM-DD."""
    return r"^\d{4}-\d{2}-\d{2}$"


def test_regex_date_split_pass(regex_date: str):
    assert _regex_split_pass(regex_date) == [
        "\\d",
        "{",
        "4",
        "}",
        "-",
        "\\d",
        "{",
        "2",
        "}",
        "-",
        "\\d",
        "{",
        "2",
        "}",
    ]


def test_regex_date_expand_pass(regex_date: str):
    I = _regex_split_pass(regex_date)
    assert _regex_expand_pass(I) == [
        "[",
        "0123456789",
        "]",
        "{",
        "4",
        "}",
        "-",
        "[",
        "0123456789",
        "]",
        "{",
        "2",
        "}",
        "-",
        "[",
        "0123456789",
        "]",
        "{",
        "2",
        "}",
    ]


def test_regex_date_negate_pass(regex_date: str):
    I = _regex_expand_pass(_regex_split_pass(regex_date))
    assert _regex_negate_pass(I) == I


@pytest.fixture
def regex_hex_color():
    """Regex to match hex color codes (e.g., #FFFFFF)."""
    return r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"


def test_regex_hex_color_split_pass(regex_hex_color: str):
    assert _regex_split_pass(regex_hex_color) == [
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


def test_regex_hex_color_expand_pass(regex_hex_color: str):
    assert _regex_expand_pass(_regex_split_pass(regex_hex_color)) == [
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


def test_regex_hex_color_negate_pass(regex_hex_color: str):
    I = _regex_expand_pass(_regex_split_pass(regex_hex_color))
    assert _regex_negate_pass(I) == I


@pytest.fixture
def regex_username():
    """Regex to match usernames with alphanumeric characters and underscores."""
    return r"^[^a-zA-Z0-9_]{3,16}$"


def test_regex_username_split_pass(regex_username: str):
    assert _regex_split_pass(regex_username) == [
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


def test_regex_username_expand_pass(regex_username: str):
    I = _regex_split_pass(regex_username)
    assert _regex_expand_pass(I) == [
        "[",
        "^abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
        "]",
        "{",
        "3,16",
        "}",
    ]


def test_regex_username_negate_pass(regex_username: str):
    I = _regex_expand_pass(_regex_split_pass(regex_username))
    assert _regex_negate_pass(I) == [
        "[",
        "!\"#$%&'()*+,-./:;<=>?@[\\]`{|}~ ",
        "]",
        "{",
        "3,16",
        "}",
    ]


@pytest.fixture
def regex_ipv4():
    """Regex to match IPv4 addresses."""
    return r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"


def test_regex_ipv4_split_pass(regex_ipv4: str):
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


def test_regex_ipv4_expand_pass(regex_ipv4: str):
    I = _regex_split_pass(regex_ipv4)
    assert _regex_expand_pass(I) == [
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


def test_regex_ipv4_negate_pass(regex_ipv4: str):
    I = _regex_expand_pass(_regex_split_pass(regex_ipv4))
    assert _regex_negate_pass(I) == I


@pytest.fixture
def regex_html_tag():
    """Regex to match simple HTML tags."""
    return r"^<([a-z]+)([^<]+)*(?:>(.*)<\/\1)>|\s+\/>)$"


def test_regex_html_tag_split_pass(regex_html_tag: str):
    with pytest.raises(InvalidRegex) as exc_info:
        _regex_split_pass(regex_html_tag)

    assert str(exc_info.value) == "Backreferences are not supported yet."


@pytest.fixture
def regex_complex_nested_groups_and_quantifiers():
    return r"((a{1,2}|b{2,3})+(c|d{1,2})*){2,5}"


def test_regex_complex_nested_groups_and_quantifiers_split_pass(
    regex_complex_nested_groups_and_quantifiers: str,
):
    assert _regex_split_pass(regex_complex_nested_groups_and_quantifiers) == [
        "(",
        "(",
        "a",
        "{",
        "1,2",
        "}",
        "|",
        "b",
        "{",
        "2,3",
        "}",
        ")",
        "+",
        "(",
        "c",
        "|",
        "d",
        "{",
        "1,2",
        "}",
        ")",
        "*",
        ")",
        "{",
        "2,5",
        "}",
    ]


@pytest.fixture
def regex_mixed_unicode_and_special_characters():
    return r"[\u00A0-\uFFFF\w\d\s]{2,}|[^\x00-\x7F]+"


def test_regex_mixed_unicode_and_special_characters_split_pass(
    regex_mixed_unicode_and_special_characters: str,
):
    with pytest.raises(InvalidRegex) as exc_info:
        _regex_split_pass(regex_mixed_unicode_and_special_characters)

    assert str(exc_info.value) == "Unicode characters are not supported yet."


@pytest.fixture
def regex_intricate_alternation_and_grouping():
    return r"(foo.(bar|baz){1,3}|qux{2,4})+(?:xyz|abc)*"


def test_regex_intricate_alternation_and_grouping_split_pass(
    regex_intricate_alternation_and_grouping: str,
):
    assert _regex_split_pass(regex_intricate_alternation_and_grouping) == [
        "(",
        "foo",
        ".",
        "(",
        "bar",
        "|",
        "baz",
        ")",
        "{",
        "1,3",
        "}",
        "|",
        "qux",
        "{",
        "2,4",
        "}",
        ")",
        "+",
        "(",
        "xyz",
        "|",
        "abc",
        ")",
        "*",
    ]


def test_regex_intricate_alternation_and_grouping_expand_pass(
    regex_intricate_alternation_and_grouping: str,
):
    assert _regex_expand_pass(
        _regex_split_pass(regex_intricate_alternation_and_grouping)
    ) == [
        "(",
        "foo",
        "[",
        "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ ",
        "]",
        "(",
        "bar",
        "|",
        "baz",
        ")",
        "{",
        "1,3",
        "}",
        "|",
        "qux",
        "{",
        "2,4",
        "}",
        ")",
        "+",
        "(",
        "xyz",
        "|",
        "abc",
        ")",
        "*",
    ]


@pytest.fixture
def regex_extreme_quantifiers_and_escaped_metacharacters():
    return r"(\.\*\?\+\\|[\{\}\[\]\(\)]){3,10}"


def test_regex_extreme_quantifiers_and_escaped_metacharacters_split_pass(
    regex_extreme_quantifiers_and_escaped_metacharacters: str,
):
    assert _regex_split_pass(regex_extreme_quantifiers_and_escaped_metacharacters) == [
        "(",
        "\\.\\*\\?\\+\\\\",
        "|",
        "[",
        "\\{\\}\\[\\]\\(\\)",
        "]",
        ")",
        "{",
        "3,10",
        "}",
    ]


def test_regex_extreme_quantifiers_and_escaped_metacharacters_expand_pass(
    regex_extreme_quantifiers_and_escaped_metacharacters: str,
):
    I = _regex_split_pass(regex_extreme_quantifiers_and_escaped_metacharacters)
    assert _regex_expand_pass(I) == I


def test_regex_extreme_quantifiers_and_escaped_metacharacters_negate_pass(
    regex_extreme_quantifiers_and_escaped_metacharacters: str,
):
    I = _regex_expand_pass(
        _regex_split_pass(regex_extreme_quantifiers_and_escaped_metacharacters)
    )
    assert _regex_negate_pass(I) == I
