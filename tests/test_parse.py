import pytest

from lextrail.build import split_definition_into_lexemes
from lextrail.guide import divide_cfg_into_productions
from lextrail.helpers import TrailError, format_error


def test_split_error_QXXX():
    example = """ /[0-9]*.[0-9]*/ | -" factor |  "(" expression ")" """

    with pytest.raises(TrailError) as exc_info:
        split_definition_into_lexemes(example)

    assert str(exc_info.value) == format_error(
        'Unclosed string literal - missing " to terminate the string.',
        ' /[0-9]*.[0-9]*/ | -" factor |  "(" expression ")',
        '"',
    )


def test_split_error_XRXX():
    example = """ "(" expression (factor "-" /[0-9]*.[0-9]* ")" """

    with pytest.raises(TrailError) as exc_info:
        split_definition_into_lexemes(example)

    assert str(exc_info.value) == format_error(
        "Unterminated regex pattern starting with `/` - add closing delimiter or escape `/` as `\\/`.",
        ' "(" expression (factor "-" ',
        "/",
    )


def test_split_error_XXGO():
    example = """ "(" expression (factor "-" /[0-9]*.[0-9]*/ ")" """

    with pytest.raises(TrailError) as exc_info:
        split_definition_into_lexemes(example)

    assert str(exc_info.value) == format_error(
        "Unmatched '(' - expected a closing ')'.",
        ' "(" expression ',
        "(",
    )


def test_split_error_XXGC():
    example = """ "(" expression factor "-" /[0-9]*.[0-9]*/) ")" """

    with pytest.raises(TrailError) as exc_info:
        split_definition_into_lexemes(example)

    assert str(exc_info.value) == format_error(
        "Unexpected `)` - no matching opening parenthesis.",
        ' "(" expression factor "-" /[0-9]*.[0-9]*/',
        ")",
    )


def test_divide_cfg_cont():
    example = """ 
    start: expression

    expression: (term (("+" | "\n") term)) | "^" expression

    term: factor (("*" | "\t") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/ 
    """

    result = divide_cfg_into_productions(example)
    correct = dict(
        {
            "start": "expression",
            "expression": '(term (("+" | "\n") term)) | "^" expression',
            "term": 'factor (("*" | "\t") factor)',
            "factor": "NUMBER",
            "NUMBER": "/-?[0-9]+/",
        }
    )

    assert result == correct


def test_divide_cfg_jump():
    example = """ 
    start: expression

    expression: (term (("+" | "\n") term)) 
    |    "^" expression

    term: factor (("*" | "\t") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/ 
    """

    result = divide_cfg_into_productions(example)
    correct = dict(
        {
            "start": "expression",
            "expression": '(term (("+" | "\n") term))    |    "^" expression',
            "term": 'factor (("*" | "\t") factor)',
            "factor": "NUMBER",
            "NUMBER": "/-?[0-9]+/",
        }
    )

    assert result == correct


def test_divide_error_name():
    example = """
    start: expression

    expression: term (("+" | "-") term)*

    ter^m: factor (("*" | "/") factor)*

    factor: NUMBER
           | "-" factor
           | "(" expression ")"

    NUMBER: /[0-9]+\\.[0-9]+/
    """

    with pytest.raises(TrailError) as exc_info:
        divide_cfg_into_productions(example)

    assert str(exc_info.value) == format_error(
        "Name `ter^m` contains special characters.",
        "",
        'ter^m: factor (("*" | "/") factor)*',
    )


def test_divide_error_duplicate():
    example = """
    start: expression

    expression: term {("+" | "-") term}

    term: factor {("*" | "/") factor}

    factor: NUMBER
           | "-" factor
           | "(" expression ")"

    factor: NUMBER

    NUMBER: /[0-9]+\\.[0-9]+/
    """

    with pytest.raises(TrailError) as exc_info:
        divide_cfg_into_productions(example)

    assert str(exc_info.value) == format_error(
        f"Duplicate production.",
        "",
        "factor: NUMBER",
    )


def test_divide_error_start():
    example = """ 
    expression: (term (("+" | "\n") term)) | "^" expression

    term: factor (("*" | "\t") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/ 
    """

    with pytest.raises(TrailError) as exc_info:
        divide_cfg_into_productions(example)

    assert str(exc_info.value) == format_error(
        "`start` production rule has not been defined.", "", ""
    )


def test_divide_error_colons():
    example = """ 
    start: expression

    expression: (term (("+" | "\n") term)) | "^" expression

    term: factor (("*" | "\t"): factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """

    with pytest.raises(TrailError) as exc_info:
        divide_cfg_into_productions(example)

    assert str(exc_info.value) == format_error(
        "Duplicate separator `:`.", "term", ': factor (("*" | "\t"):'
    )
