import random

from lark import Lark
import pytest
from lextrail.guide import trail_cfg, get_next_values
from lextrail.helpers import TrailError, format_error


def simulate_response(cfg: str) -> str:
    trail = trail_cfg(cfg)
    response, value = [], ""

    while values := get_next_values(trail, value):
        value = random.choice(values)
        response.append(value)

    return "".join(response)


def test_cfg_PXXX01():
    example = r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """

    response = simulate_response(example)

    lark = Lark(
        example,
        parser="lalr",
    )

    assert lark.parse(response)


def test_cfg_PXSX02():
    example = r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor (("*" | "/") factor)?

    factor: NUMBER

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """

    response = simulate_response(example)

    lark = Lark(
        example,
        parser="lalr",
    )

    assert lark.parse(response)


def test_cfg_PXSL03():
    example = r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor (("*" | "/") factor)*

    factor: NUMBER

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """

    response = simulate_response(example)

    lark = Lark(
        example,
        parser="lalr",
    )

    assert lark.parse(response)


def test_cfg_PXSL04():
    example = r"""
    start: expression

    expression: term (("+" | "-") term)*

    term: factor (("*" | "/") factor)?

    factor: NUMBER

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """

    response = simulate_response(example)

    lark = Lark(
        example,
        parser="lalr",
    )

    assert lark.parse(response)


def test_cfg_PRSL05():
    example = r"""
    start: expression

    expression: term (("+" | "-") term)*

    term: factor (("*" | "/") factor "^")

    factor: NUMBER

    NUMBER: /[0-9]*\.[0-9]*/
    """

    response = simulate_response(example)

    lark = Lark(
        example,
        parser="lalr",
    )

    assert lark.parse(response)


def test_cfg_PRSX06():
    example = r"""
    start: expression

    expression: term (("+" | "-") term)?

    term: factor (("*" | "/") factor "^" /-?[0-9]+/)?

    factor: NUMBER

    NUMBER: /[0-9]*\.[0-9]*/
    """

    response = simulate_response(example)

    lark = Lark(
        example,
        parser="lalr",
    )

    assert lark.parse(response)


def test_cfg_PRSL07():
    example = r"""
    start: expression

    expression: term (("+" | "-") term "^" /-?[0-9]+/)*

    term: factor (("*" | "/") factor "^" /-?[0-9]+/)?

    factor: NUMBER

    NUMBER: /[0-9]*\.[0-9]*/
    """

    response = simulate_response(example)

    lark = Lark(
        example,
        parser="lalr",
    )

    assert lark.parse(response)


def test_cfg_PRSL08():
    example = r"""
    start: expression

    expression: term (("+" | "-") term "^" /-?[0-9]+/)*

    term: factor (("*" | "/") factor "^" /-?[0-9]+/)?

    factor: NUMBER

    NUMBER: /[0-9]*\.[0-9]*/
    """

    response = simulate_response(example)

    lark = Lark(
        example,
        parser="lalr",
    )

    assert lark.parse(response)


def test_cfg_warning_01():
    example = r"""
    start: expression

    expression: term (("+" | expression) term)

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """

    with pytest.warns(UserWarning) as record:
        trail_cfg(example)
        assert (
            str(record[0].message)
            == 'A potential loop of non-terminal symbols exists in expression: term (("+" | expression) term).'
        )


def test_cfg_warning_02():
    example = r"""
    start: expression

    expression: expression | (term (("+" | "-") term))

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """

    with pytest.warns(UserWarning) as record:
        trail_cfg(example)
        assert (
            str(record[0].message)
            == 'A potential loop of non-terminal symbols exists in expression: expression | (term (("+" | "-") term)).'
        )


def test_cfg_warning_03():
    example = r"""
    start: expression

    expression: (term (("+" | "-") term)) | "^" expression

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """

    with pytest.warns(UserWarning) as record:
        trail_cfg(example)
        assert (
            str(record[0].message)
            == 'A potential loop of non-terminal symbols exists in expression: (term (("+" | "-") term)) | "^" expression.'
        )


def test_cfg_warning_04():
    example = r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor (("*" | "/") term factor)*

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """

    with pytest.warns(UserWarning) as record:
        trail_cfg(example)
        assert (
            str(record[0].message)
            == 'A potential loop of non-terminal symbols exists in term: factor (("*" | "/") term factor)*.'
        )


def test_cfg_warning_05():
    example = r"""
    start: expression

    expression: term (expression ("+" | "-") term)?

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """

    with pytest.warns(UserWarning) as record:
        trail_cfg(example)
        assert (
            str(record[0].message)
            == 'A potential loop of non-terminal symbols exists in expression: term (expression ("+" | "-") term)?.'
        )


def test_cfg_loop():
    example = r"""
    start: expression

    expression: term expression (("+" | "-") term)

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """

    with pytest.raises(TrailError) as exc_info:
        trail_cfg(example)

    assert str(exc_info.value) == format_error(
        "Production has an infinite loop.",
        "expression: ",
        'term expression (("+" | "-") term)',
    )


def test_cfg_undefined():
    example = r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor (("*" | "/") factor)

    factor: NUMBER
    """

    with pytest.raises(TrailError) as exc_info:
        trail_cfg(example)

    assert str(exc_info.value) == format_error(
        "Production has an undefined variable `NUMBER`.",
        "factor: ",
        "NUMBER",
    )
