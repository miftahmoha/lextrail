from dataclasses import dataclass, field
from typing import Callable, Optional

import exrex
import pytest
from lark import Lark
from transformers import AutoTokenizer

from cfg_parse.base import Symbol
from cfg_parse.cfg_build.build import _get_symbol_from_content_attr_for_seq
from cfg_parse.cfg_guide.guide import CFGGenerationState, CFGGuide
from cfg_parse.cfg_guide.helpers import (
    _extract_str_from_symbols,
    _get_next_terminal_symbols_as_regex,
    _retrace_symbol_obj_from_str,
    update_for_possible_single_token_combinations,
)
from cfg_parse.converter import _convert_to_lark_syntax
from cfg_parse.exceptions import InfiniteLoop


@dataclass
class _MockLLM:
    response: str = field(default="")

    # Use `exrex` to generate a sample from a REGEX expression.
    def get_choice(self, regex_str: str) -> str:
        choice = exrex.getone(regex_str)
        if choice == "END_DEF":
            return choice
        self.response += choice[1:-1]
        return choice


def _get_guided_response(cfg_guide_obj: CFGGuide) -> str:
    mock_llm = _MockLLM()
    chosen_symbol: Optional[Symbol] = None
    chosen_symbol_hist: CFGGenerationState = None

    while True:
        cfg_guide_obj.get_next_terminals(chosen_symbol_hist, chosen_symbol)
        next_terminals_w_hist = cfg_guide_obj.next_terminals_w_history

        # End generation.
        if not next_terminals_w_hist:
            break

        next_terminal_symbols = list(next_terminals_w_hist.keys())
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

    term: factor {("*" | "/") factor "^" regex("-?[0-9]+")}

    factor: NUMBER

    NUMBER: regex("[0-9]*\.[0-9]*")
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


test_cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any(
    r"""
    start: expression

    expression: term {("+" | "-") term}

    term: factor {("*" | "/") factor "^" regex("-?[0-9]+")}

    factor: NUMBER

    NUMBER: regex("[0-9]*\.[0-9]*")
    """
)


@pytest.fixture
def cfg_without_infinite_loops_with_regex_with_special_delimiters_none_once():
    return r"""
    start: expression

    expression: term [("+" | "-") term]

    term: factor [("*" | "/") factor "^" regex("-?[0-9]+")]

    factor: NUMBER

    NUMBER: regex("[0-9]*\.[0-9]*")
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

    expression: term {("+" | "-") term "^" regex("-?[0-9]+")}

    term: factor [("*" | "/") factor "^" regex("-?[0-9]+")]

    factor: NUMBER

    NUMBER: regex("[0-9]*\.[0-9]*")
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

    NUMBER: regex("-?[0-9]+")
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

    NUMBER: regex("-?[0-9]+")
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

    NUMBER: regex("-?[0-9]+")
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

    NUMBER: regex("-?[0-9]+")
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


@pytest.fixture
def gpt2_encoder() -> Callable[[str], list[int]]:
    tokenizer = AutoTokenizer.from_pretrained("gpt2")

    def encode(text: str) -> list[int]:
        return tokenizer(text)["input_ids"]

    return encode


def encode(text: str) -> list[int]:
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    return tokenizer(text)["input_ids"]


@pytest.fixture
def cfg_with_single_token_combination():
    return r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: "{" "\"" regex("-?[0-9]+")
    """


def test_cfg_with_single_token_combination(
    cfg_with_single_token_combination: str, gpt2_encoder: Callable[[str], list[int]]
):
    cfg_object = CFGGuide(cfg_with_single_token_combination)
    cfg_object.get_next_terminals(None, None)

    next_terminals_w_hist_w_update = update_for_possible_single_token_combinations(
        cfg_object, gpt2_encoder
    )

    symbol_comb = _get_symbol_from_content_attr_for_seq(
        list(next_terminals_w_hist_w_update.keys()), '"{""'
    )[0]
    symbols_str = _extract_str_from_symbols(list(next_terminals_w_hist_w_update.keys()))

    # Checking the combinations.
    assert symbols_str == ['"{"', '"{""']

    # Checking the path for the combination symbol.
    assert next_terminals_w_hist_w_update[symbol_comb][-1].state.content == '"""'  # type: ignore


@pytest.fixture
def cfg_with_double_token_bracket_combination_one_level():
    return r"""
    start: expression

    expression: " " "{" "\"" regex("-?[0-9]+")
    """


def test_cfg_with_double_token_bracket_combination(
    cfg_with_double_token_bracket_combination_one_level: str,
    gpt2_encoder: Callable[[str], list[int]],
):
    cfg_object = CFGGuide(cfg_with_double_token_bracket_combination_one_level)
    cfg_object.get_next_terminals(None, None)

    next_terminals_w_hist_w_update = update_for_possible_single_token_combinations(
        cfg_object, gpt2_encoder
    )

    symbol_comb = _get_symbol_from_content_attr_for_seq(
        list(next_terminals_w_hist_w_update.keys()), '" {""'
    )[0]
    symbols_str = _extract_str_from_symbols(list(next_terminals_w_hist_w_update.keys()))

    # Checking the combinations.
    assert symbols_str == ['" "', '" {"', '" {""']

    # Checking the path for the combination symbol.
    assert next_terminals_w_hist_w_update[symbol_comb][-1].state.content == '"""'  # type: ignore


@pytest.fixture
def cfg_with_double_token_less_combination_two_level():
    return r"""
    start: expression

    expression: ("*" | "/") factor

    factor: " " "<" "/" regex("-?[0-9]+")
    """


def test_cfg_with_double_token_less_combination_two_level(
    cfg_with_double_token_less_combination_two_level: str,
    gpt2_encoder: Callable[[str], list[int]],
):
    cfg_object = CFGGuide(cfg_with_double_token_less_combination_two_level)
    cfg_object.get_next_terminals(None, None)

    # Get "*" or "/" symbol.
    symbol_level_0 = _get_symbol_from_content_attr_for_seq(
        list(cfg_object.next_terminals_w_history), '"/"'
    )[0]
    cfg_generation_state_level_0 = cfg_object.next_terminals_w_history[symbol_level_0]

    # Go a level further.
    cfg_object.get_next_terminals(cfg_generation_state_level_0, symbol_level_0)

    next_terminals_w_hist_w_update = update_for_possible_single_token_combinations(
        cfg_object, gpt2_encoder
    )

    symbol_comb = _get_symbol_from_content_attr_for_seq(
        list(next_terminals_w_hist_w_update.keys()), '" </"'
    )[0]
    symbols_str = _extract_str_from_symbols(list(next_terminals_w_hist_w_update.keys()))

    # Checking the combinations.
    assert symbols_str == ['" "', '" <"', '" </"']

    # Checking the path for the combination symbol.
    assert next_terminals_w_hist_w_update[symbol_comb][-1].state.content == '"/"'  # type: ignore


# test_cfg_with_double_token_less_combination_two_level(
#     r"""
#     start: expression

#     expression: ("*" | "/") factor

#     factor: " " "<" "/" regex("-?[0-9]+")
#     """,
#     encode,
# )


# @pytest.fixture
# def llama_encoder() -> Callable[[str], list[int]]:
#     tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")

#     def encode(text: str) -> list[int]:
#         return tokenizer(text)["input_ids"]

#     return encode


# @pytest.fixture
# def cfg_with_double_token_less_combination_two_level_sep():
#     return r"""
#     start: expression

#     expression: " " term

#     term: "<" factor

#     factor: "/" regex("-?[0-9]+")
#     """


# def test_cfg_with_double_token_less_combination_two_level_sep(
#     cfg_with_double_token_less_combination_two_level_sep: str,
#     gpt2_encoder: Callable[[str], list[int]],
# ):
#     cfg_object = CFGGuide(cfg_with_double_token_less_combination_two_level_sep)
#     cfg_object.get_next_terminals(None, None)

#     # Get "*" or "/" symbol.
#     symbol_level_0 = _get_symbol_from_content_attr_for_seq(
#         list(cfg_object.next_terminals_w_history), '"/"'
#     )[0]
#     cfg_generation_state_level_0 = cfg_object.next_terminals_w_history[symbol_level_0]

#     # Go a level further.
#     cfg_object.get_next_terminals(cfg_generation_state_level_0, symbol_level_0)

#     next_terminals_w_hist_w_update = update_for_possible_single_token_combinations(
#         cfg_object, gpt2_encoder
#     )

#     symbol_comb = _get_symbol_from_content_attr_for_seq(
#         list(next_terminals_w_hist_w_update.keys()), '" </"'
#     )[0]
#     symbols_str = _extract_str_from_symbols(list(next_terminals_w_hist_w_update.keys()))

#     # Checking the combinations.
#     assert symbols_str == ['" "', '" <"', '" </"']

#     # Checking the path for the combination symbol.
#     assert next_terminals_w_hist_w_update[symbol_comb][-1].state.content == '"/"'  # type: ignore
