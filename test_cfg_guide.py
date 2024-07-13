from dataclasses import dataclass, field

import pytest
import exrex

from lark import Lark

from cfg_parse.base import Symbol
from cfg_parse.cfg_guide.guide import CFGGenerationState, CFGGuide
from cfg_parse.cfg_guide.helpers import (
    _get_next_terminal_symbols_as_regex,
    _retrace_symbol_obj_from_str,
)
from cfg_parse.converter import _convert_to_lark_syntax
from cfg_parse.exceptions import InfiniteLoop


@dataclass
class _MockLLM:
    response: str = field(default="")

    # Use `exrex` to generate a sample from a REGEX expression.
    def get_choice(self, regex_str: str) -> str:
        choice = exrex.getone(regex_str)
        if choice == "EOS_SYMBOL":
            return choice
        self.response += choice[1:-1]
        return choice


def _get_guided_response(cfg_guide_obj: CFGGuide) -> str:
    mock_llm = _MockLLM()
    chosen_symbol: Symbol = None
    chosen_symbol_hist: CFGGenerationState = None

    while True:
        cfg_guide_obj.get_next_terminals(chosen_symbol_hist, chosen_symbol)
        next_terminals_w_hist = cfg_guide_obj.next_terminals_w_history

        # End generation.
        if not next_terminals_w_hist:
            break

        next_terminal_symbols = next_terminals_w_hist.keys()
        regex = _get_next_terminal_symbols_as_regex(next_terminal_symbols)

        # Get the chosen symbol as a string from the LLM.
        choice = mock_llm.get_choice(regex)

        # Get the symbol object.
        chosen_symbol = _retrace_symbol_obj_from_str(
            choice,
            next_terminal_symbols,
        )

        chosen_symbol_hist = next_terminals_w_hist[chosen_symbol]

    return mock_llm.response


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

    response = _get_guided_response(cfg_guide_obj)

    parser = Lark(
        _convert_to_lark_syntax(
            cfg_without_infinite_loops_without_regex_without_special_delimiters
        ),
        parser="lalr",
    )
    assert parser.parse(response)


@pytest.fixture
def cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any():
    return r"""
    start: expression
    
    expression: term (("+" | "-") term)

    term: factor {("*" | "/") factor}

    factor: NUMBER 

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """


def test_cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any(
    cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any: str,
):
    cfg_guide_obj = CFGGuide(
        cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any
    )

    response = _get_guided_response(cfg_guide_obj)

    parser = Lark(
        _convert_to_lark_syntax(
            cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any
        ),
        parser="lalr",
    )
    assert parser.parse(response)


@pytest.fixture
def cfg_without_infinite_loops_without_regex_with_special_delimiters_none_once():
    return r"""
    start: expression
    
    expression: term (("+" | "-") term)

    term: factor [("*" | "/") factor]

    factor: NUMBER 

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """


def test_cfg_without_infinite_loops_without_regex_with_special_delimiters_none_once(
    cfg_without_infinite_loops_without_regex_with_special_delimiters_none_once: str,
):
    cfg_guide_obj = CFGGuide(
        cfg_without_infinite_loops_without_regex_with_special_delimiters_none_once
    )

    response = _get_guided_response(cfg_guide_obj)

    parser = Lark(
        _convert_to_lark_syntax(
            cfg_without_infinite_loops_without_regex_with_special_delimiters_none_once
        ),
        parser="lalr",
    )
    assert parser.parse(response)


@pytest.fixture
def cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any_once():
    return r"""
    start: expression
    
    expression: term {("+" | "-") term}

    term: factor [("*" | "/") factor]

    factor: NUMBER 

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """


def test_cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any_once(
    cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any_once: str,
):
    cfg_guide_obj = CFGGuide(
        cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any_once
    )

    response = _get_guided_response(cfg_guide_obj)

    parser = Lark(
        _convert_to_lark_syntax(
            cfg_without_infinite_loops_without_regex_with_special_delimiters_none_any_once
        ),
        parser="lalr",
    )
    assert parser.parse(response)


@pytest.fixture
def cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any():
    return r"""
    start: expression
    
    expression: term {("+" | "-") term}

    term: factor {("*" | "/") factor "^" Regex("-?[0-9]+")}

    factor: NUMBER 

    NUMBER: Regex("[0-9]*\.[0-9]*")
    """


def test_cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any(
    cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any: str,
):
    cfg_guide_obj = CFGGuide(
        cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any
    )

    response = _get_guided_response(cfg_guide_obj)

    parser = Lark(
        _convert_to_lark_syntax(
            cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any
        ),
        parser="lalr",
    )
    assert parser.parse(response)


@pytest.fixture
def cfg_without_infinite_loops_with_regex_with_special_delimiters_none_once():
    return r"""
    start: expression
    
    expression: term [("+" | "-") term]

    term: factor [("*" | "/") factor "^" Regex("-?[0-9]+")]

    factor: NUMBER 

    NUMBER: Regex("[0-9]*\.[0-9]*")
    """


def test_cfg_without_infinite_loops_with_regex_with_special_delimiters_none_once(
    cfg_without_infinite_loops_with_regex_with_special_delimiters_none_once: str,
):
    cfg_guide_obj = CFGGuide(
        cfg_without_infinite_loops_with_regex_with_special_delimiters_none_once
    )

    response = _get_guided_response(cfg_guide_obj)

    parser = Lark(
        _convert_to_lark_syntax(
            cfg_without_infinite_loops_with_regex_with_special_delimiters_none_once
        ),
        parser="lalr",
    )
    assert parser.parse(response)


@pytest.fixture
def cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any_once():
    return r"""
    start: expression
    
    expression: term {("+" | "-") term "^" Regex("-?[0-9]+")}

    term: factor [("*" | "/") factor "^" Regex("-?[0-9]+")]

    factor: NUMBER 

    NUMBER: Regex("[0-9]*\.[0-9]*")
    """


def test_cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any_once(
    cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any_once: str,
):
    cfg_guide_obj = CFGGuide(
        cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any_once
    )

    response = _get_guided_response(cfg_guide_obj)

    parser = Lark(
        _convert_to_lark_syntax(
            cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any_once
        ),
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

    NUMBER: Regex("-?[0-9]+")
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

    NUMBER: Regex("-?[0-9]+")
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

    NUMBER: Regex("-?[0-9]+")
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

    NUMBER: Regex("-?[0-9]+")
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
