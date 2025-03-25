import pytest
from lark import Lark

import sys

sys.path.append("/home/achraf/lextrail")

from lextrail.exceptions import InfiniteLoop
from lextrail.guide.guide import CFGGuide
from lextrail.utils.simulate import _get_full_guided_response

from lextrail.helpers import LTContext


@pytest.fixture
def cfg_without_infinite_loops_without_regex_without_special_delimiters():
    return r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """


def test_cfg_without_infinite_loops_without_regex_without_special_delimiters(
    cfg_without_infinite_loops_without_regex_without_special_delimiters: str,
):
    cfg_guide_obj = CFGGuide(
        cfg_without_infinite_loops_without_regex_without_special_delimiters
    )

    response = _get_full_guided_response(cfg_guide_obj)

    parser = Lark(
        cfg_without_infinite_loops_without_regex_without_special_delimiters,
        parser="lalr",
    )
    assert parser.parse(response)


@pytest.fixture
def cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any():
    return r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor (("*" | "/") factor)*

    factor: NUMBER

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """


def test_cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any(
    cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any: str,
):
    cfg_guide_obj = CFGGuide(
        cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any
    )

    response = _get_full_guided_response(cfg_guide_obj)

    parser = Lark(
        cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any,
        parser="lalr",
    )
    assert parser.parse(response)


@pytest.fixture
def cfg_without_infinite_loops_without_regex_with_special_delimiters_none_once():
    return r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor (("*" | "/") factor)?

    factor: NUMBER

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """


def test_cfg_without_infinite_loops_without_regex_with_special_delimiters_none_once(
    cfg_without_infinite_loops_without_regex_with_special_delimiters_none_once: str,
):
    cfg_guide_obj = CFGGuide(
        cfg_without_infinite_loops_without_regex_with_special_delimiters_none_once
    )

    response = _get_full_guided_response(cfg_guide_obj)

    parser = Lark(
        cfg_without_infinite_loops_without_regex_with_special_delimiters_none_once,
        parser="lalr",
    )
    assert parser.parse(response)


@pytest.fixture
def cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any_once():
    return r"""
    start: expression

    expression: term (("+" | "-") term)*

    term: factor (("*" | "/") factor)?

    factor: NUMBER

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """


def test_cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any_once(
    cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any_once: str,
):
    cfg_guide_obj = CFGGuide(
        cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any_once
    )

    response = _get_full_guided_response(cfg_guide_obj)

    parser = Lark(
        cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any_once,
        parser="lalr",
    )
    assert parser.parse(response)


@pytest.fixture
def cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any():
    return r"""
    start: expression

    expression: term (("+" | "-") term)*

    term: factor (("*" | "/") factor "^" /-?[0-9]+/)?

    factor: NUMBER

    NUMBER: /[0-9]*\.[0-9]*/
    """


def test_cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any(
    cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any: str,
):
    with LTContext(PARSE_REGEX = "1"):
        cfg_guide_obj = CFGGuide(
            cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any
        )

    response = _get_full_guided_response(cfg_guide_obj)

    parser = Lark(
        cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any,
        parser="lalr",
    )
    assert parser.parse(response)


@pytest.fixture
def cfg_without_infinite_loops_with_regex_with_special_delimiters_none_once():
    return r"""
    start: expression

    expression: term (("+" | "-") term)?

    term: factor (("*" | "/") factor "^" /-?[0-9]+/)?

    factor: NUMBER

    NUMBER: /[0-9]*\.[0-9]*/
    """


def test_cfg_without_infinite_loops_with_regex_with_special_delimiters_none_once(
    cfg_without_infinite_loops_with_regex_with_special_delimiters_none_once: str,
):
    with LTContext(PARSE_REGEX = "1"):
        cfg_guide_obj = CFGGuide(
            cfg_without_infinite_loops_with_regex_with_special_delimiters_none_once
        )

    response = _get_full_guided_response(cfg_guide_obj)

    parser = Lark(
        cfg_without_infinite_loops_with_regex_with_special_delimiters_none_once,
        parser="lalr",
    )
    assert parser.parse(response)


@pytest.fixture
def cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any_once():
    return r"""
    start: expression

    expression: term (("+" | "-") term "^" /-?[0-9]+/)*

    term: factor (("*" | "/") factor "^" /-?[0-9]+/)?

    factor: NUMBER

    NUMBER: /[0-9]*\.[0-9]*/
    """


def test_cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any_once(
    cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any_once: str,
):
    with LTContext(PARSE_REGEX = "1"):
        cfg_guide_obj = CFGGuide(
            cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any_once
        )

        response = _get_full_guided_response(cfg_guide_obj)

        parser = Lark(
            cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any_once,
            parser="lalr",
        )
        assert parser.parse(response)


@pytest.fixture
def cfg_with_infinite_loops_with_inside_or_escape():
    return r"""
    start: expression

    expression: term (("+" | expression) term)

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """


def test_cfg_with_infinite_loops_with_in_or_escape(
    cfg_with_infinite_loops_with_inside_or_escape: str,
):
    with pytest.warns(UserWarning) as record:
        CFGGuide(cfg_with_infinite_loops_with_inside_or_escape)
        assert (
            str(record[0].message)
            == 'A potential loop of non-terminal symbols exists in expression: term (("+" | expression) term).'
        )


@pytest.fixture
def cfg_with_infinite_loops_with_outside_or_escape():
    return r"""
    start: expression

    expression: (term (("+" | "-") term)) | "^" expression

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """


def test_cfg_with_infinite_loops_with_outside_or_escape(
    cfg_with_infinite_loops_with_outside_or_escape: str,
):
    with pytest.warns(UserWarning) as record:
        CFGGuide(cfg_with_infinite_loops_with_outside_or_escape)
        assert (
            str(record[0].message)
            == 'A potential loop of non-terminal symbols exists in expression: (term (("+" | "-") term)) | "^" expression.'
        )


@pytest.fixture
def cfg_with_infinite_loops_with_none_any_escape():
    return r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor {("*" | "/") term factor}

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """


def test_cfg_with_infinite_loops_with_none_any_escape(
    cfg_with_infinite_loops_with_none_any_escape: str,
):
    with pytest.warns(UserWarning) as record:
        CFGGuide(cfg_with_infinite_loops_with_none_any_escape)
        assert (
            str(record[0].message)
            == 'A potential loop of non-terminal symbols exists in term: factor {("*" | "/") term factor}.'
        )


@pytest.fixture
def cfg_with_infinite_loops_with_none_once_escape():
    return r"""
    start: expression

    expression: term [expression ("+" | "-") term]

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """


def test_cfg_with_infinite_loops_with_none_once_escape(
    cfg_with_infinite_loops_with_none_once_escape: str,
):
    with pytest.warns(UserWarning) as record:
        CFGGuide(cfg_with_infinite_loops_with_none_once_escape)
        assert (
            str(record[0].message)
            == 'A potential loop of non-terminal symbols exists in expression: term [expression ("+" | "-") term].'
        )


@pytest.fixture
def cfg_with_infinite_loops_without_escape():
    return r"""
    start: expression

    expression: term expression (("+" | "-") term)

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """


def test_cfg_with_infinite_loops_without_escape(
    cfg_with_infinite_loops_without_escape: str,
):
    with pytest.raises(InfiniteLoop) as exc_info:
        CFGGuide(cfg_with_infinite_loops_without_escape)

    assert (
        str(exc_info.value)
        == 'An infinite loop of non-terminal symbols `expression -> expression` is found in expression: term expression (("+" | "-") term).'
    )
