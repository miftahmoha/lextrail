import pytest

from lextrail.build.passes import split_definition_into_lexemes
from lextrail.guide.passes import divide_cfg_into_rules, split_cfg_into_lines


@pytest.fixture
def def_with_out_or_no_special_delimiters():
    return """ "(" expression ( (factor "-") |  /[0-9]*.[0-9]*/) ")" """


def test_split_definition_into_lexemes_def_with_out_or_no_special_delimiters(
    def_with_out_or_no_special_delimiters: str,
):
    result = split_definition_into_lexemes(def_with_out_or_no_special_delimiters)

    assert result == split_definition_into_lexemes(
        def_with_out_or_no_special_delimiters.replace(" ", "")
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
    return """ "(" expression ((factor "-")+ | (/[0-9]*.[0-9]*/ | "+")+) ")" """


def test_split_definition_into_lexemes_def_with_in_and_out_or_with_special_delimiters_once_any(
    def_with_in_and_out_or_with_special_delimiters_once_any: str,
):
    result = split_definition_into_lexemes(
        def_with_in_and_out_or_with_special_delimiters_once_any
    )

    assert result == split_definition_into_lexemes(
        def_with_in_and_out_or_with_special_delimiters_once_any.replace(" ", "")
    )
    assert result == [
        '"("',
        "expression",
        "(",
        "{",
        "(",
        "factor",
        '"-"',
        ")",
        "}",
        "|",
        "{",
        "(",
        "/[0-9]*.[0-9]*/",
        "|",
        '"+"',
        ")",
        "}",
        ")",
        '")"',
    ]


@pytest.fixture
def def_with_in_and_out_ext_or_seq_with_special_delimiters_none_any():
    return """ "(" expression ((factor "-") ("+" power) | (/[0-9]*.[0-9]*/ factor | "+" expression)*)* ")" """


def test_split_definition_into_lexemes_def_with_in_and_out_ext_or_seq_with_special_delimiters_none_any(
    def_with_in_and_out_ext_or_seq_with_special_delimiters_none_any: str,
):
    result = split_definition_into_lexemes(
        def_with_in_and_out_ext_or_seq_with_special_delimiters_none_any
    )

    assert result == [
        '"("',
        "expression",
        "{",
        "[",
        "(",
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
        "[",
        "(",
        "/[0-9]*.[0-9]*/",
        "factor",
        "|",
        '"+"',
        "expression",
        ")",
        "]",
        "}",
        ")",
        "]",
        "}",
        '")"',
    ]


@pytest.fixture
def def_with_in_and_out_ext_or_seq_with_special_delimiters_none_once():
    return """ "(" expression ((factor "-") ("+" power) | (/[0-9]*.[0-9]*/ factor | "+" expression)?)? ")" """


def test_split_definition_into_lexemes_def_with_in_and_out_ext_or_seq_with_special_delimiters_none_once(
    def_with_in_and_out_ext_or_seq_with_special_delimiters_none_once: str,
):
    lexemes = split_definition_into_lexemes(
        def_with_in_and_out_ext_or_seq_with_special_delimiters_none_once
    )

    assert lexemes == [
        '"("',
        "expression",
        "[",
        "(",
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
        "(",
        "/[0-9]*.[0-9]*/",
        "factor",
        "|",
        '"+"',
        "expression",
        ")",
        "]",
        ")",
        "]",
        '")"',
    ]


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_once_any():
    return """ "(" expression ((factor "-")+ ("/" factor) ("+" power)? expression (/[0-9]*.[0-9]*/ "*") | (/[0-9]*.[0-9]*/ factor | "+" expression)?)* ")" """


def test_split_definition_into_lexemes_def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_once_any(
    def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_once_any: str,
):
    lexemes = split_definition_into_lexemes(
        def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_once_any
    )

    assert lexemes == [
        '"("',
        "expression",
        "{",
        "[",
        "(",
        "{",
        "(",
        "factor",
        '"-"',
        ")",
        "}",
        "(",
        '"/"',
        "factor",
        ")",
        "[",
        "(",
        '"+"',
        "power",
        ")",
        "]",
        "expression",
        "(",
        "/[0-9]*.[0-9]*/",
        '"*"',
        ")",
        "|",
        "[",
        "(",
        "/[0-9]*.[0-9]*/",
        "factor",
        "|",
        '"+"',
        "expression",
        ")",
        "]",
        ")",
        "]",
        "}",
        '")"',
    ]


@pytest.fixture
def cfg_without_escapes_no_raw():
    return """
    start: expression

    expression: (term (("+" | "-") term)) | "^" expression

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """


def test_split_cfg_grammar_without_escapes_no_raw(
    cfg_without_escapes_no_raw: str,
):
    lines = [line.strip() for line in split_cfg_into_lines(cfg_without_escapes_no_raw)]

    assert lines == [
        "start: expression",
        'expression: (term (("+" | "-") term)) | "^" expression',
        'term: factor (("*" | "/") factor)',
        "factor: NUMBER",
        "NUMBER: /-?[0-9]+/",
    ]


def test_divide_cfg_grammar_into_rules_without_escapes_no_raw(
    cfg_without_escapes_no_raw: str,
):
    rules: dict[str, str] = divide_cfg_into_rules(cfg_without_escapes_no_raw)

    assert rules == {
        "start": "expression",
        "expression": '(term (("+" | "-") term)) | "^" expression',
        "term": 'factor (("*" | "/") factor)',
        "factor": "NUMBER",
        "NUMBER": "/-?[0-9]+/",
    }


@pytest.fixture
def cfg_with_escapes_no_raw():
    return """
    start: expression

    expression: (term (("+" | "\n") term)) | "^" expression

    term: factor (("*" | "\t") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """


def test_split_cfg_grammar_with_escapes_no_raw(
    cfg_with_escapes_no_raw: str,
):
    lines = [line.strip() for line in split_cfg_into_lines(cfg_with_escapes_no_raw)]

    assert lines == [
        "start: expression",
        'expression: (term (("+" | "\n") term)) | "^" expression',
        'term: factor (("*" | "\t") factor)',
        "factor: NUMBER",
        "NUMBER: /-?[0-9]+/",
    ]


def test_divide_cfg_grammar_into_rules_with_escapes_no_raw(
    cfg_with_escapes_no_raw: str,
):
    rules: dict[str, str] = divide_cfg_into_rules(cfg_with_escapes_no_raw)

    assert rules == {
        "start": "expression",
        "expression": '(term (("+" | "\n") term)) | "^" expression',
        "term": 'factor (("*" | "\t") factor)',
        "factor": "NUMBER",
        "NUMBER": "/-?[0-9]+/",
    }


@pytest.fixture
def cfg_with_multlines_no_raw():
    return """
    start: expression

    expression: (term (("+" | "\n") term))
    | "^" expression

    term: factor (("*" | "\t") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """


def test_split_cfg_grammar_with_multlines_no_raw(
    cfg_with_multlines_no_raw: str,
):
    lines = [line.strip() for line in split_cfg_into_lines(cfg_with_multlines_no_raw)]

    assert lines == [
        "start: expression",
        'expression: (term (("+" | "\n") term))',
        '| "^" expression',
        'term: factor (("*" | "\t") factor)',
        "factor: NUMBER",
        "NUMBER: /-?[0-9]+/",
    ]


def test_divide_cfg_grammar_into_rules_with_multlines_no_raw(
    cfg_with_multlines_no_raw: str,
):
    rules: dict[str, str] = divide_cfg_into_rules(cfg_with_multlines_no_raw)

    assert rules == {
        "start": "expression",
        "expression": '(term (("+" | "\n") term)) | "^" expression',
        "term": 'factor (("*" | "\t") factor)',
        "factor": "NUMBER",
        "NUMBER": "/-?[0-9]+/",
    }
