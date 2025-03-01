import pytest
from itertools import groupby

from lextrail.guide.guide import Guide

@pytest.fixture
def def_without_or_without_nesting_standard():
    return '"1" ("2" "3") "4" ("5" "6") "7"'


def test_def_without_or_without_nesting_standard(def_without_or_without_nesting_standard):
    Guide_ = Guide(def_without_or_without_nesting_standard)
    
    chosen_symbols, chosen_states = [], []
    while True: 
        Guide_.get_next_terminals(chosen_symbols, chosen_states)
        chosen_symbols, chosen_states = list(Guide_.next_terminals_w_history.keys()), list(Guide_.next_terminals_w_history.values())

        if not Guide_.next_terminals_w_history:
            break

    assert Guide_.backreferences == {1: "1234567", 2: "23", 3: "56"} 


@pytest.fixture
def def_without_or_without_nesting_successive_standard():
    return '"1" ("2" "3" "4") ("5" "6") "7"'


def test_def_without_or_without_nesting_successive_standard(def_without_or_without_nesting_successive_standard):
    Guide_ = Guide(def_without_or_without_nesting_successive_standard)
    
    chosen_symbols, chosen_states = [], []
    while True: 
        Guide_.get_next_terminals(chosen_symbols, chosen_states)
        chosen_symbols, chosen_states = list(Guide_.next_terminals_w_history.keys()), list(Guide_.next_terminals_w_history.values())

        if not Guide_.next_terminals_w_history:
            break

    assert Guide_.backreferences == {1: "1234567", 2: "234", 3: "56"} 


@pytest.fixture
def def_without_or_with_nesting_standard():
    return '"1" ("2" ("3" "4") "5" ("6" "7") "8") "9" "10"'


def test_def_without_or_with_nesting_standard(def_without_or_with_nesting_standard):
    Guide_ = Guide(def_without_or_with_nesting_standard)
    
    chosen_symbols, chosen_states = [], []
    while True: 
        Guide_.get_next_terminals(chosen_symbols, chosen_states)
        chosen_symbols, chosen_states = list(Guide_.next_terminals_w_history.keys()), list(Guide_.next_terminals_w_history.values())

        if not Guide_.next_terminals_w_history:
            break

    assert Guide_.backreferences == {1: "12345678910", 2: "2345678", 3: "34", 4: "67"} 


@pytest.fixture
def def_without_or_with_nesting_successive_standard():
    return '"1" ("2" ("3" "4" "5") ("6" "7") "8") "9" "10"'


def test_def_without_or_with_nesting_successive_standard(def_without_or_with_nesting_successive_standard):
    Guide_ = Guide(def_without_or_with_nesting_successive_standard)
    
    chosen_symbols, chosen_states = [], []
    while True: 
        Guide_.get_next_terminals(chosen_symbols, chosen_states)
        chosen_symbols, chosen_states = list(Guide_.next_terminals_w_history.keys()), list(Guide_.next_terminals_w_history.values())

        if not Guide_.next_terminals_w_history:
            break

    assert Guide_.backreferences == {1: "12345678910", 2: "2345678", 3: "345", 4: "67"} 


@pytest.fixture
def def_with_or_with_nesting_standard():
    return '"1" ("2" ("3" "4") "5" | "6" ("7" "8") "9") "10" "11"'


def test_def_with_or_with_successive_standard(def_with_or_with_nesting_standard):
    Guide_ = Guide(def_with_or_with_nesting_standard)
    
    chosen_symbols, chosen_states = [], []
    while True: 
        Guide_.get_next_terminals(chosen_symbols, chosen_states) # type: ignore
        if not Guide_.next_terminals_w_history:
            break
        chosen_symbols, chosen_states = list(Guide_.next_terminals_w_history.keys())[0], list(Guide_.next_terminals_w_history.values())[0]

    assert Guide_.backreferences == {1: "123457891011", 2: "2345789", 3: "34", 4: "78"} 


@pytest.fixture
def def_with_or_with_nesting_successive_standard():
    return '"1" ("2" ("3" "4" "5") | ("6" "7") "8") "9" "10"'


def test_def_with_or_with_nesting_successive_standard(def_with_or_with_nesting_successive_standard):
    Guide_ = Guide(def_with_or_with_nesting_successive_standard)
    
    chosen_symbols, chosen_states = [], []
    while True: 
        Guide_.get_next_terminals(chosen_symbols, chosen_states) # type: ignore
        if not Guide_.next_terminals_w_history:
            break
        chosen_symbols, chosen_states = list(Guide_.next_terminals_w_history.keys())[0], list(Guide_.next_terminals_w_history.values())[0]

    assert Guide_.backreferences == {1: "123458910", 2: "23458", 3: "345"} 


def count_successive_pairs(lst):
    result = []
    count = 0
    i = 0
    while i < len(lst) - 1:
        if lst[i] == 0 and lst[i + 1] == 0:
            count += 1
            i += 1  # Skip the next element to avoid overlapping
        else:
            if count > 0:
                result.append(count)
                count = 0
        i += 1
    if count > 0:
        result.append(count)
    return result


@pytest.fixture
def def_without_or_without_nesting_none_any():
    return '"1" {"2" "3"} "4" {"5" "6"} "7"'


@pytest.mark.parametrize("choices, counts", [
    ([0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0], (3, 2)),
    ([0, 0, 0, 1, 1, 0], (1, 0)),
    ([0, 1, 1, 1, 0], (0, 0)),
    ([0, 1,  0,  0, 1, 0], (0, 1)),
    ([0, 0, 0, 1, 0, 0, 1, 0], (1, 1)),
    ([0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0], (2, 3)),
])
def test_def_without_or_without_nesting_none_any(def_without_or_without_nesting_none_any, choices, counts):
    Guide_ = Guide(def_without_or_without_nesting_none_any)
    
    chosen_symbols, chosen_states = [], []
    while True: 
        Guide_.get_next_terminals(chosen_symbols, chosen_states) # type: ignore
        if not Guide_.next_terminals_w_history:
            break
        choice = choices.pop(0)
        chosen_symbols, chosen_states = list(Guide_.next_terminals_w_history.keys())[choice], list(Guide_.next_terminals_w_history.values())[choice]

    assert Guide_.backreferences == {k: v for k, v in {1: "1" + "23"*counts[0] + "4" + "56"*counts[1] + "7", 2: "23"*counts[0], 3: "56"*counts[1]}.items() if v != ""}


@pytest.fixture
def def_without_or_with_nesting_none_any():
    return '"1" {"2" {"3" "4"} "5"} "6" {"7" "8"} "9"'


@pytest.mark.parametrize("choices, counts", [
    ([0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0], (1, 2, 2)),
    ([0, 0, 1, 1, 1, 1], (1, 0, 0)),
    ([0, 1, 1], (0, 0, 0)),
    ([0, 1,  0,  0, 0, 0, 0, 0, 1], (0, 0, 3)),
    ([0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1], (2, 2, 2)),
])
def test_def_without_or_with_nesting_none_any(def_without_or_with_nesting_none_any, choices, counts):
    Guide_ = Guide(def_without_or_with_nesting_none_any)
    
    chosen_symbols, chosen_states = [], []
    while True: 
        Guide_.get_next_terminals(chosen_symbols, chosen_states) # type: ignore
        if not Guide_.next_terminals_w_history:
            break
        choice = choices.pop(0)
        chosen_symbols, chosen_states = list(Guide_.next_terminals_w_history.keys())[choice], list(Guide_.next_terminals_w_history.values())[choice]

    assert Guide_.backreferences == {k: v for k, v in {1: "1" + ("2" + "34"*counts[1] + "5")*counts[0] + "6" + "78"*counts[2] + "9", 2: ("2" + "34"*counts[1] + "5")*counts[0], 3: "34"*counts[0]*counts[1], 4: "78"*counts[2]}.items() if v != ""}
