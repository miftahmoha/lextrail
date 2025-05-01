import pytest

from lextrail.assemble import (
    AssemblyGraph,
    _assemble_graph,
    _update_single_token_combinations,
)
from lextrail.guide import CFGGuide
from lextrail.helpers import (
    _extract_content_from_symbols,
    _fetch_terminal_from_content_in_sequence,
)

gpt2_vocabulary_subset = [
    "ing",  # Common suffix
    "tion",  # Common suffix for nouns
    "pre",  # Common prefix
    "un",  # Negation prefix
    "able",  # Common suffix
    "ment",  # Common suffix
    "inter",  # Common prefix
    "ness",  # Common suffix
    "ate",  # Verb suffix
    "ology",  # Study of something
    "ize",  # Verb suffix
    "ship",  # Common suffix (relationship, friendship)
    "ful",  # Common adjective suffix
    "less",  # Common adjective suffix
    "ism",  # Common suffix for beliefs/practices
    "ance",  # Common noun suffix
    "ence",  # Common noun suffix
    "anti",  # Common prefix meaning against
    "micro",  # Common prefix meaning small
    "poly",  # Common prefix meaning many
]


@pytest.fixture
def gpt2_vocabulary_subset_as_graphs():
    return _assemble_graph(gpt2_vocabulary_subset)


@pytest.fixture
def cfg_with_uni_level_combination_no_or_uni_choice():
    return r"""
    start: level

    level: "o" "l" "o" "g" "y"
    """


def test_cfg_with_uni_level_combination_no_or_uni_choice(
    cfg_with_uni_level_combination_no_or_uni_choice: str,
    gpt2_vocabulary_subset_as_graphs: AssemblyGraph,
):
    cfg_object = CFGGuide(cfg_with_uni_level_combination_no_or_uni_choice)
    cfg_object.get_next_terminals()

    next_terminals_w_hist_w_update = _update_single_token_combinations(
        cfg_object, gpt2_vocabulary_subset_as_graphs
    )

    combination_as_symbol = _fetch_terminal_from_content_in_sequence(
        list(next_terminals_w_hist_w_update.keys()), '"ology"'
    )[0]

    next_terminals_as_str = _extract_content_from_symbols(
        list(next_terminals_w_hist_w_update.keys())
    )

    # Checking the combinations.
    assert next_terminals_as_str == ['"o"', '"ology"']

    # Checking the path for the combination symbol.
    assert next_terminals_w_hist_w_update[combination_as_symbol][-1].state.content == '"y"'  # type: ignore


@pytest.fixture
def cfg_with_mlt_level_combination_no_or_uni_choice():
    return r"""
    start: level_0

    level_0: "a" level_1

    level_1: "b" level_2

    level_2: "l" level_3

    level_3: "e"
    """


def test_cfg_with_mlt_level_combination_no_or_uni_choice(
    cfg_with_mlt_level_combination_no_or_uni_choice: str,
    gpt2_vocabulary_subset_as_graphs: AssemblyGraph,
):
    cfg_object = CFGGuide(cfg_with_mlt_level_combination_no_or_uni_choice)
    cfg_object.get_next_terminals()

    next_terminals_w_hist_w_update = _update_single_token_combinations(
        cfg_object, gpt2_vocabulary_subset_as_graphs
    )

    combination_as_symbol = _fetch_terminal_from_content_in_sequence(
        list(next_terminals_w_hist_w_update.keys()), '"able"'
    )[0]

    next_terminals_as_str = _extract_content_from_symbols(
        list(next_terminals_w_hist_w_update.keys())
    )

    # Checking the combinations.
    assert next_terminals_as_str == ['"a"', '"able"']

    # Checking the path for the combination symbol.
    assert next_terminals_w_hist_w_update[combination_as_symbol][-1].state.content == '"e"'  # type: ignore


@pytest.fixture
def cfg_with_mlt_level_combination_mlt_or_uni_choice():
    return r"""
    start: level_0

    level_0: ("o" | "a") level_1

    level_1: ("l" | "b") level_2

    level_2: ("o" | "l") level_3

    level_3: ("g" | "e") level_4

    level_4: "y"
    """


def test_cfg_with_mlt_level_combination_mlt_or_uni_choice(
    cfg_with_mlt_level_combination_mlt_or_uni_choice: str,
    gpt2_vocabulary_subset_as_graphs: AssemblyGraph,
):
    cfg_object = CFGGuide(cfg_with_mlt_level_combination_mlt_or_uni_choice)
    cfg_object.get_next_terminals()

    next_terminals_w_hist_w_update = _update_single_token_combinations(
        cfg_object, gpt2_vocabulary_subset_as_graphs
    )

    next_terminals_as_str = _extract_content_from_symbols(
        list(next_terminals_w_hist_w_update.keys())
    )

    # Checking the combinations.
    assert next_terminals_as_str == ['"o"', '"a"', '"ology"', '"able"']

    # Checking the path for the combination symbols.
    for terminal_as_str in next_terminals_as_str:
        terminal_as_symbol = _fetch_terminal_from_content_in_sequence(
            list(next_terminals_w_hist_w_update.keys()), terminal_as_str
        )[0]
        assert next_terminals_w_hist_w_update[terminal_as_symbol][-1].state.content == f'"{terminal_as_str[-2]}"'  # type: ignore


@pytest.fixture
def cfg_with_mlt_level_combination_uni_or_mlt_choice():
    return r"""
    start: level_0

    level_0: ("a" | "e") level_1

    level_1: "n" level_2

    level_2: "c" level_3

    level_3: "e"
    """


def test_cfg_with_mlt_level_combination_uni_or_mlt_choice(
    cfg_with_mlt_level_combination_uni_or_mlt_choice: str,
    gpt2_vocabulary_subset_as_graphs: AssemblyGraph,
):
    cfg_object = CFGGuide(cfg_with_mlt_level_combination_uni_or_mlt_choice)
    cfg_object.get_next_terminals()

    next_terminals_w_hist_w_update = _update_single_token_combinations(
        cfg_object, gpt2_vocabulary_subset_as_graphs
    )

    next_terminals_as_str = _extract_content_from_symbols(
        list(next_terminals_w_hist_w_update.keys())
    )

    # Checking the combinations.
    assert next_terminals_as_str == ['"a"', '"e"', '"ance"', '"ence"']

    # Checking the path for the combination symbols.
    for terminal_as_str in next_terminals_as_str:
        terminal_as_symbol = _fetch_terminal_from_content_in_sequence(
            list(next_terminals_w_hist_w_update.keys()), terminal_as_str
        )[0]
        assert next_terminals_w_hist_w_update[terminal_as_symbol][-1].state.content == f'"{terminal_as_str[-2]}"'  # type: ignore


def test_int_with_mlt_level_combination_uni_or_mlt_choice(
    cfg_with_mlt_level_combination_uni_or_mlt_choice: str,
    gpt2_vocabulary_subset_as_graphs: AssemblyGraph,
):
    cfg_object = CFGGuide(cfg_with_mlt_level_combination_uni_or_mlt_choice)

    cfg_object.set_assembler(gpt2_vocabulary_subset_as_graphs)

    cfg_object.get_next_terminals()

    next_terminals_as_str = _extract_content_from_symbols(
        list(cfg_object.next_terminals_w_states.keys())
    )

    # Checking the combinations.
    assert next_terminals_as_str == ['"a"', '"e"', '"ance"', '"ence"']

    # Checking the path for the combination symbols.
    for terminal_as_str in next_terminals_as_str:
        terminal_as_symbol = _fetch_terminal_from_content_in_sequence(
            list(cfg_object.next_terminals_w_states.keys()), terminal_as_str
        )[0]
        assert cfg_object.next_terminals_w_states[terminal_as_symbol][-1].state.content == f'"{terminal_as_str[-2]}"'  # type: ignore


test_vocabulary_subset = ["A", "B", "ADE", "BDE", "BCE", "ADEF", "BCEF"]


@pytest.fixture
def test_vocabulary_subset_as_graphs():
    return _assemble_graph(test_vocabulary_subset)


@pytest.fixture
def cfg_with_mlt_level_combination_mlt_or_mlt_choice():
    return r"""
    start: level_0

    level_0: ("A" | "B") level_1

    level_1: ("C" | "D") level_2

    level_2: "E" level_3

    level_3: "F"
    """


def test_cfg_with_mlt_level_combination_mlt_or_mlt_choice(
    cfg_with_mlt_level_combination_mlt_or_mlt_choice: str,
    test_vocabulary_subset_as_graphs: AssemblyGraph,
):
    cfg_object = CFGGuide(cfg_with_mlt_level_combination_mlt_or_mlt_choice)
    cfg_object.get_next_terminals()

    next_terminals_w_hist_w_update = _update_single_token_combinations(
        cfg_object, test_vocabulary_subset_as_graphs
    )

    next_terminals_as_str = _extract_content_from_symbols(
        list(next_terminals_w_hist_w_update.keys())
    )

    # Checking the combinations.
    assert next_terminals_as_str == [
        '"A"',
        '"B"',
        '"ADE"',
        '"ADEF"',
        '"BCE"',
        '"BCEF"',
        '"BDE"',
    ]

    # Checking the path for the combination symbols.
    for terminal_as_str in next_terminals_as_str:
        terminal_as_symbol = _fetch_terminal_from_content_in_sequence(
            list(next_terminals_w_hist_w_update.keys()), terminal_as_str
        )[0]
        assert next_terminals_w_hist_w_update[terminal_as_symbol][-1].state.content == f'"{terminal_as_str[-2]}"'  # type: ignore


def test_int_with_mlt_level_combination_mlt_or_mlt_choice(
    cfg_with_mlt_level_combination_mlt_or_mlt_choice: str,
    test_vocabulary_subset_as_graphs: AssemblyGraph,
):
    cfg_object = CFGGuide(cfg_with_mlt_level_combination_mlt_or_mlt_choice)

    cfg_object.set_assembler(test_vocabulary_subset_as_graphs)

    cfg_object.get_next_terminals()

    next_terminals_as_str = _extract_content_from_symbols(
        list(cfg_object.next_terminals_w_states.keys())
    )

    # Checking the combinations.
    assert next_terminals_as_str == [
        '"A"',
        '"B"',
        '"ADE"',
        '"ADEF"',
        '"BCE"',
        '"BCEF"',
        '"BDE"',
    ]

    # Checking the path for the combination symbols.
    for terminal_as_str in next_terminals_as_str:
        terminal_as_symbol = _fetch_terminal_from_content_in_sequence(
            list(cfg_object.next_terminals_w_states.keys()), terminal_as_str
        )[0]
        assert cfg_object.next_terminals_w_states[terminal_as_symbol][-1].state.content == f'"{terminal_as_str[-2]}"'  # type: ignore
