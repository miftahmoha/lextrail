from typing import Callable

import pytest
from lark import Lark
from transformers import AutoTokenizer

from lextrail.guide.guide import CFGGuide
from lextrail.guide.passes import update_for_possible_single_token_combinations
from lextrail.render.simulate import _get_full_guided_response
from lextrail.helpers import (
    _fetch_terminal_from_content_in_sequence,
    _extract_content_from_symbols,
)
from lextrail.exceptions import InfiniteLoop


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

    term: factor (("*" | "/") factor "^" /-?[0-9]+/)*

    factor: NUMBER

    NUMBER: /[0-9]*\.[0-9]*/
    """


def test_cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any(
    cfg_without_infinite_loops_with_regex_with_special_delimiters_none_any: str,
):
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

    NUMBER: "{" "\"" /-?[0-9]+/
    """


def test_cfg_with_single_token_combination(
    cfg_with_single_token_combination: str, gpt2_encoder: Callable[[str], list[int]]
):
    cfg_object = CFGGuide(cfg_with_single_token_combination)
    cfg_object.get_next_terminals(None, None)

    next_terminals_w_hist_w_update = update_for_possible_single_token_combinations(
        cfg_object, gpt2_encoder
    )

    symbol_comb = _fetch_terminal_from_content_in_sequence(
        list(next_terminals_w_hist_w_update.keys()), '"{""'
    )[0]
    symbols_str = _extract_content_from_symbols(
        list(next_terminals_w_hist_w_update.keys())
    )

    # Checking the combinations.
    assert symbols_str == ['"{"', '"{""']

    # Checking the path for the combination symbol.
    assert next_terminals_w_hist_w_update[symbol_comb][-1].state.content == '"""'  # type: ignore


@pytest.fixture
def cfg_with_double_token_bracket_combination_one_level():
    return r"""
    start: expression

    expression: " " "{" "\"" /-?[0-9]+/
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

    symbol_comb = _fetch_terminal_from_content_in_sequence(
        list(next_terminals_w_hist_w_update.keys()), '" {""'
    )[0]
    symbols_str = _extract_content_from_symbols(
        list(next_terminals_w_hist_w_update.keys())
    )

    # Checking the combinations.
    assert symbols_str == ['" "', '" {"', '" {""']

    # Checking the path for the combination symbol.
    assert next_terminals_w_hist_w_update[symbol_comb][-1].state.content == '"""'  # type: ignore


@pytest.fixture
def cfg_with_double_token_less_combination_two_level():
    return r"""
    start: expression

    expression: ("*" | "/") factor

    factor: " " "<" "/" /-?[0-9]+/
    """


def test_cfg_with_double_token_less_combination_two_level(
    cfg_with_double_token_less_combination_two_level: str,
    gpt2_encoder: Callable[[str], list[int]],
):
    cfg_object = CFGGuide(cfg_with_double_token_less_combination_two_level)
    cfg_object.get_next_terminals(None, None)

    # Get "*" or "/" symbol.
    symbol_level_0 = _fetch_terminal_from_content_in_sequence(
        list(cfg_object.next_terminals_w_history), '"/"'
    )[0]
    cfg_generation_state_level_0 = cfg_object.next_terminals_w_history[symbol_level_0]

    # Go a level further.
    cfg_object.get_next_terminals(cfg_generation_state_level_0, symbol_level_0)

    next_terminals_w_hist_w_update = update_for_possible_single_token_combinations(
        cfg_object, gpt2_encoder
    )

    symbol_comb = _fetch_terminal_from_content_in_sequence(
        list(next_terminals_w_hist_w_update.keys()), '" </"'
    )[0]
    symbols_str = _extract_content_from_symbols(
        list(next_terminals_w_hist_w_update.keys())
    )

    # Checking the combinations.
    assert symbols_str == ['" "', '" <"', '" </"']

    # Checking the path for the combination symbol.
    assert next_terminals_w_hist_w_update[symbol_comb][-1].state.content == '"/"'  # type: ignore


# @pytest.fixture
# def llama_encoder() -> Callable[[str], list[int]]:
#     # tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")
#     tokenizer = AutoTokenizer.from_pretrained("gpt2")

#     def encode(text: str) -> list[int]:
#         return tokenizer(text)["input_ids"]

#     return encode


@pytest.fixture
def cfg_with_double_token_less_combination_mult_level():
    return r"""
    start: expression

    expression: " " term

    term: "<" factor

    factor: "/" /-?[0-9]+/
    """


def test_cfg_with_double_token_less_combination_mult_level(
    cfg_with_double_token_less_combination_mult_level: str,
    gpt2_encoder: Callable[[str], list[int]],
):
    cfg_object = CFGGuide(cfg_with_double_token_less_combination_mult_level)
    cfg_object.get_next_terminals(None, None)
    next_terminals_w_hist_w_update = update_for_possible_single_token_combinations(
        cfg_object, gpt2_encoder
    )
    symbol_comb = _fetch_terminal_from_content_in_sequence(
        list(next_terminals_w_hist_w_update.keys()), '" </"'
    )[0]
    symbols_str = _extract_content_from_symbols(
        list(next_terminals_w_hist_w_update.keys())
    )

    # Checking the combinations.
    assert symbols_str == ['" "', '" <"', '" </"']

    # Checking the path for the combination symbol.
    assert next_terminals_w_hist_w_update[symbol_comb][-1].state.content == '"/"'  # type: ignore


@pytest.fixture
def cfg_with_double_token_less_combination_mult_level_w_init():
    return r"""
    start: "*" expression

    expression: " " term

    term: "<" factor

    factor: "/" /-?[0-9]+/
    """


def test_cfg_with_double_token_less_combination_mult_level_w_init(
    cfg_with_double_token_less_combination_mult_level_w_init: str,
    gpt2_encoder: Callable[[str], list[int]],
):
    cfg_object = CFGGuide(cfg_with_double_token_less_combination_mult_level_w_init)
    cfg_object.get_next_terminals(None, None)

    # Get "*" or "/" symbol.
    symbol_level_0 = _fetch_terminal_from_content_in_sequence(
        list(cfg_object.next_terminals_w_history), '"*"'
    )[0]
    cfg_generation_state_level_0 = cfg_object.next_terminals_w_history[symbol_level_0]

    # Go a level further.
    cfg_object.get_next_terminals(cfg_generation_state_level_0, symbol_level_0)

    next_terminals_w_hist_w_update = update_for_possible_single_token_combinations(
        cfg_object, gpt2_encoder
    )
    symbol_comb = _fetch_terminal_from_content_in_sequence(
        list(next_terminals_w_hist_w_update.keys()), '" </"'
    )[0]
    symbols_str = _extract_content_from_symbols(
        list(next_terminals_w_hist_w_update.keys())
    )

    # Checking the combinations.
    assert symbols_str == ['" "', '" <"', '" </"']

    # Checking the path for the combination symbol.
    assert next_terminals_w_hist_w_update[symbol_comb][-1].state.content == '"/"'  # type: ignore


@pytest.fixture
def cfg_with_double_token_less_combination_mult_level_w_init_w_or():
    return """
    start: "*" expression

    expression: " " term

    term: ("<"|"d") factor

    factor: "/" /-?[0-9]+/
    """


def test_cfg_with_double_token_less_combination_mult_level_w_init_w_or(
    cfg_with_double_token_less_combination_mult_level_w_init_w_or: str,
    gpt2_encoder: Callable[[str], list[int]],
):
    cfg_object = CFGGuide(cfg_with_double_token_less_combination_mult_level_w_init_w_or)
    cfg_object.get_next_terminals(None, None)

    # Get "*" or "/" symbol.
    symbol_level_0 = _fetch_terminal_from_content_in_sequence(
        list(cfg_object.next_terminals_w_history), '"*"'
    )[0]
    cfg_generation_state_level_0 = cfg_object.next_terminals_w_history[symbol_level_0]

    # Go a level further.
    cfg_object.get_next_terminals(cfg_generation_state_level_0, symbol_level_0)

    next_terminals_w_hist_w_update = update_for_possible_single_token_combinations(
        cfg_object, gpt2_encoder
    )
    symbol_comb_00 = _fetch_terminal_from_content_in_sequence(
        list(next_terminals_w_hist_w_update.keys()), '" </"'
    )[0]
    symbol_comb_01 = _fetch_terminal_from_content_in_sequence(
        list(next_terminals_w_hist_w_update.keys()), '" <"'
    )[0]
    symbol_comb_02 = _fetch_terminal_from_content_in_sequence(
        list(next_terminals_w_hist_w_update.keys()), '" d"'
    )[0]
    symbols_str = _extract_content_from_symbols(
        list(next_terminals_w_hist_w_update.keys())
    )

    # Checking the combinations.
    assert symbols_str == ['" "', '" <"', '" d"', '" </"']

    # Checking the path for the combination symbol.
    assert next_terminals_w_hist_w_update[symbol_comb_00][-1].state.content == '"/"'  # type: ignore
    assert next_terminals_w_hist_w_update[symbol_comb_01][-1].state.content == '"<"'  # type: ignore
    assert next_terminals_w_hist_w_update[symbol_comb_02][-1].state.content == '"d"'  # type: ignore
