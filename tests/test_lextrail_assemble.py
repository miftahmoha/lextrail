import pytest

from lextrail.guide import get_next_proposals, trail_cfg
from lextrail.assemble import get_asm_proposals


@pytest.fixture
def gpt_vocabulary_subset():
    return [
        "able",
        "ology",
        "ance",
        "ence",
    ]


@pytest.fixture
def cfg_with_uni_level_combination_no_or_uni_choice():
    return r"""
    start: level

    level: "o" "l" "o" "g" "y" "<"
    """


def test_cfg_with_uni_level_combination_no_or_uni_choice(
    cfg_with_uni_level_combination_no_or_uni_choice: str,
    gpt_vocabulary_subset: list[str],
):
    trail = trail_cfg(
        cfg_with_uni_level_combination_no_or_uni_choice, gpt_vocabulary_subset
    )

    proposals = get_next_proposals(trail, [])

    assert [proposal.symbol.content for proposal in proposals] == ["o"]

    proposals = get_asm_proposals(trail, proposals)

    assert [proposal.symbol.content for proposal in proposals] == ["ology"]

    # The assembled symbol must inherit the connections from the last symbol.
    for proposal in proposals:
        proposal.state[-1].graph.tree[proposal.symbol][0].content == "<"


@pytest.fixture
def cfg_with_mlt_level_combination_no_or_uni_choice():
    return r"""
    start: level_0

    level_0: "a" level_1

    level_1: "b" level_2

    level_2: "l" level_3

    level_3: "e" "<"
    """


def test_cfg_with_mlt_level_combination_no_or_uni_choice(
    cfg_with_mlt_level_combination_no_or_uni_choice: str,
    gpt_vocabulary_subset: list[str],
):
    trail = trail_cfg(
        cfg_with_mlt_level_combination_no_or_uni_choice, gpt_vocabulary_subset
    )

    proposals = get_next_proposals(trail, [])

    assert [proposal.symbol.content for proposal in proposals] == ["a"]

    proposals = get_asm_proposals(trail, proposals)

    assert [proposal.symbol.content for proposal in proposals] == ["able"]

    # The assembled symbol must inherit the connections from the last symbol.
    for proposal in proposals:
        proposal.state[-1].graph.tree[proposal.symbol][0].content == "<"


@pytest.fixture
def cfg_with_mlt_level_combination_mlt_or_uni_choice():
    return r"""
    start: level_0

    level_0: ("o" | "a") level_1

    level_1: ("l" | "b") level_2

    level_2: ("o" | "l") level_3

    level_3: ("g" | "e" "<") level_4

    level_4: "y" "<"
    """


def test_cfg_with_mlt_level_combination_mlt_or_uni_choice(
    cfg_with_mlt_level_combination_mlt_or_uni_choice: str,
    gpt_vocabulary_subset: list[str],
):
    trail = trail_cfg(
        cfg_with_mlt_level_combination_mlt_or_uni_choice, gpt_vocabulary_subset
    )

    proposals = get_next_proposals(trail, [])

    assert [proposal.symbol.content for proposal in proposals] == ["o", "a"]

    proposals = get_asm_proposals(trail, proposals)

    assert [proposal.symbol.content for proposal in proposals] == ["ology", "able"]

    # The assembled symbol must inherit the connections from the last symbol.
    for proposal in proposals:
        proposal.state[-1].graph.tree[proposal.symbol][0].content == "<"


@pytest.fixture
def cfg_with_mlt_level_combination_uni_or_mlt_choice():
    return r"""
    start: level_0

    level_0: ("a" | "e") level_1

    level_1: "n" level_2

    level_2: "c" level_3

    level_3: "e" "<"
    """


def test_cfg_with_mlt_level_combination_uni_or_mlt_choice(
    cfg_with_mlt_level_combination_uni_or_mlt_choice: str,
    gpt_vocabulary_subset: list[str],
):
    trail = trail_cfg(
        cfg_with_mlt_level_combination_uni_or_mlt_choice, gpt_vocabulary_subset
    )

    proposals = get_next_proposals(trail, [])

    assert [proposal.symbol.content for proposal in proposals] == ["a", "e"]

    proposals = get_asm_proposals(trail, proposals)

    assert [proposal.symbol.content for proposal in proposals] == ["ance", "ence"]

    # The assembled symbol must inherit the connections from the last symbol.
    for proposal in proposals:
        proposal.state[-1].graph.tree[proposal.symbol][0].content == "<"


@pytest.fixture
def mix_vocabulary_subset():
    return ["A", "B", "ADE", "BDE", "BCE", "ADEF", "BCEF"]


@pytest.fixture
def cfg_with_mlt_level_combination_mlt_or_mlt_choice():
    return r"""
    start: level_0

    level_0: ("A" | "B") "<"? level_1

    level_1: ("C" | "D") level_2

    level_2: "E" "<"? level_3

    level_3: "F" "<"
    """


def test_cfg_with_mlt_level_combination_mlt_or_mlt_choice(
    cfg_with_mlt_level_combination_mlt_or_mlt_choice: str,
    mix_vocabulary_subset: list[str],
):
    trail = trail_cfg(
        cfg_with_mlt_level_combination_mlt_or_mlt_choice, mix_vocabulary_subset
    )

    proposals = get_next_proposals(trail, [])

    assert [proposal.symbol.content for proposal in proposals] == ["A", "B"]

    proposals = get_asm_proposals(trail, proposals)

    assert [proposal.symbol.content for proposal in proposals] == [
        "A",
        "ADE",
        "ADEF",
        "B",
        "BCE",
        "BCEF",
        "BDE",
    ]

    # The assembled symbol must inherit the connections from the last symbol.
    for proposal in proposals:
        assert proposal.state[-1].graph.tree[proposal.symbol][0].content == "<"
