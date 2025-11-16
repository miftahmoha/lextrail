import random

import pytest
from lark import Lark

from lextrail.exceptions import InfiniteLoop
from lextrail.guide import Trail, TrailProposal, get_next_proposals, trail_cfg
from lextrail.helpers import TrailContext, is_end_def_symbol


def simulate_response(trail: Trail) -> str:
    proposals: list[TrailProposal] = []
    response: list[str] = []

    while proposals := get_next_proposals(trail, proposals):
        choice = random.choice(proposals)
        if not is_end_def_symbol(symbol := choice.symbol):
            response.append(symbol.content)
        proposals = [choice]

    return "".join(proposal for proposal in response)


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
    trail = trail_cfg(
        cfg_without_infinite_loops_without_regex_without_special_delimiters
    )

    response = simulate_response(trail)

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
    trail = trail_cfg(
        cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any
    )

    response = simulate_response(trail)

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
    trail = trail_cfg(
        cfg_without_infinite_loops_without_regex_with_special_delimiters_none_once
    )

    response = simulate_response(trail)

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
    trail = trail_cfg(
        cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any_once
    )

    response = simulate_response(trail)

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
    with TrailContext(PARSE_REGEX="1", PARSE_TESTS="0"):
        trail = trail_cfg(
            cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any
        )

        response = simulate_response(trail)

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
    with TrailContext(PARSE_REGEX="1", PARSE_TESTS="0"):
        trail = trail_cfg(
            cfg_without_infinite_loops_with_regex_with_special_delimiters_none_once
        )

        response = simulate_response(trail)

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
    with TrailContext(PARSE_REGEX="1", PARSE_TESTS="0"):
        trail = trail_cfg(
            cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any_once
        )

        response = simulate_response(trail)

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
        trail_cfg(cfg_with_infinite_loops_with_inside_or_escape)
        assert (
            str(record[0].message)
            == 'A potential loop of non-terminal symbols exists in expression: term (("+" | expression) term).'
        )


@pytest.fixture
def cfg_with_infinite_loops_with_initial_escape():
    return r"""
    start: expression

    expression: expression | (term (("+" | "-") term))

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """


def test_cfg_with_infinite_loops_with_initial_escape(
    cfg_with_infinite_loops_with_initial_escape: str,
):
    with pytest.warns(UserWarning) as record:
        trail_cfg(cfg_with_infinite_loops_with_initial_escape)
        assert (
            str(record[0].message)
            == 'A potential loop of non-terminal symbols exists in expression: expression | (term (("+" | "-") term)).'
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
        trail_cfg(cfg_with_infinite_loops_with_outside_or_escape)
        assert (
            str(record[0].message)
            == 'A potential loop of non-terminal symbols exists in expression: (term (("+" | "-") term)) | "^" expression.'
        )


@pytest.fixture
def cfg_with_infinite_loops_with_none_any_escape():
    return r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor (("*" | "/") term factor)*

    factor: NUMBER

    NUMBER: /-?[0-9]+/
    """


def test_cfg_with_infinite_loops_with_none_any_escape(
    cfg_with_infinite_loops_with_none_any_escape: str,
):
    with pytest.warns(UserWarning) as record:
        trail_cfg(cfg_with_infinite_loops_with_none_any_escape)
        assert (
            str(record[0].message)
            == 'A potential loop of non-terminal symbols exists in term: factor (("*" | "/") term factor)*.'
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
        trail_cfg(cfg_with_infinite_loops_with_none_once_escape)
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
        trail_cfg(cfg_with_infinite_loops_without_escape)

    assert (
        str(exc_info.value)
        == 'An infinite loop of non-terminal symbols `expression -> expression` is found in expression: term expression (("+" | "-") term).'
    )
