import pytest

from lextrail.guide import get_next_proposals, trail_expr
from lextrail.helpers import TrailContext


@pytest.fixture
def def_without_or_without_nesting_standard():
    return '(?<1>"1" (?<2> "2" "3") "4" (?<3> "5" "6") "7")'


def test_def_without_or_without_nesting_standard(
    def_without_or_without_nesting_standard,
):
    trail, proposals = trail_expr(def_without_or_without_nesting_standard), []

    while proposals := get_next_proposals(trail, proposals):
        proposals = [proposals[0]]

    assert trail.backrefs == {"1": "1234567", "2": "23", "3": "56"}


@pytest.fixture
def def_without_or_without_nesting_successive_standard():
    return '(?<1> "1" (?<2> "2" "3" "4") (?<3> "5" "6") "7")'


def test_def_without_or_without_nesting_successive_standard(
    def_without_or_without_nesting_successive_standard,
):
    trail, proposals = (
        trail_expr(def_without_or_without_nesting_successive_standard),
        [],
    )

    while proposals := get_next_proposals(trail, proposals):
        proposals = [proposals[0]]

    assert trail.backrefs == {"1": "1234567", "2": "234", "3": "56"}


@pytest.fixture
def def_without_or_with_nesting_standard():
    return '(?<1> "1" (?<2> "2" (?<3> "3" "4") "5" (?<4> "6" "7") "8") "9" "10")'


def test_def_without_or_with_nesting_standard(
    def_without_or_with_nesting_standard,
):
    trail, proposals = (
        trail_expr(def_without_or_with_nesting_standard),
        [],
    )

    while proposals := get_next_proposals(trail, proposals):
        proposals = [proposals[0]]

    assert trail.backrefs == {"1": "12345678910", "2": "2345678", "3": "34", "4": "67"}


@pytest.fixture
def def_without_or_with_nesting_successive_standard():
    return '(?<1> "1" (?<2> "2" (?<3> "3" "4" "5") (?<4> "6" "7") "8") "9" "10")'


def test_def_without_or_with_nesting_successive_standard(
    def_without_or_with_nesting_successive_standard,
):
    trail, proposals = (
        trail_expr(def_without_or_with_nesting_successive_standard),
        [],
    )

    while proposals := get_next_proposals(trail, proposals):
        proposals = [proposals[0]]

    assert trail.backrefs == {"1": "12345678910", "2": "2345678", "3": "345", "4": "67"}


@pytest.fixture
def def_with_or_with_nesting_standard():
    return '(?<1> "1" (?<2> "2" (?<3> "3" "4") "5" | "6" (?<4> "7" "8") "9") "10" "11")'


def test_def_with_or_with_nesting_standard(
    def_with_or_with_nesting_standard,
):
    trail, proposals = (
        trail_expr(def_with_or_with_nesting_standard),
        [],
    )

    while proposals := get_next_proposals(trail, proposals):
        print(proposals[0].symbol.content)
        proposals = [proposals[0]]

    assert trail.backrefs == {
        "1": "123451011",
        "2": "2345",
        "3": "34",
    }


@pytest.fixture
def def_with_or_with_nesting_successive_standard():
    return '(?<1> "1" (?<2> "2" (?<3> "3" "4" "5") | ("6" "7") "8") "9" "10")'


def test_def_with_or_with_nesting_successive_standard(
    def_with_or_with_nesting_successive_standard,
):
    trail, proposals = (
        trail_expr(def_with_or_with_nesting_successive_standard),
        [],
    )

    while proposals := get_next_proposals(trail, proposals):
        proposals = [proposals[0]]

    assert trail.backrefs == {
        "1": "12345910",
        "2": "2345",
        "3": "345",
    }


@pytest.fixture
def def_without_or_without_nesting_none_any():
    return '(?<1> "1" (?<2> "2" "3")* "4" (?<3> "5" "6")* "7")'


@pytest.mark.parametrize(
    "choices, counts",
    [
        ([0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0], (3, 2)),
        ([0, 0, 0, 1, 1, 0], (1, 0)),
        ([0, 1, 1, 1, 0], (0, 0)),
        ([0, 1, 0, 0, 1, 0], (0, 1)),
        ([0, 0, 0, 1, 0, 0, 1, 0], (1, 1)),
        ([0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0], (2, 3)),
    ],
)
def test_def_without_or_without_nesting_none_any(
    def_without_or_without_nesting_none_any, choices, counts
):
    trail, proposals = trail_expr(def_without_or_without_nesting_none_any), []

    while proposals := get_next_proposals(trail, proposals):
        proposals = [proposals[choices.pop(0)]]

    assert trail.backrefs == {
        k: v
        for k, v in {
            "1": "1" + "23" * counts[0] + "4" + "56" * counts[1] + "7",
            "2": "23" * counts[0],
            "3": "56" * counts[1],
        }.items()
        if v != ""
    }


@pytest.fixture
def def_without_or_with_nesting_none_any():
    return '(?<1> "1" (?<2> "2" (?<3> "3" "4")* "5")* "6" (?<4> "7" "8")* "9")'


@pytest.mark.parametrize(
    "choices, counts",
    [
        ([0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0], ((1, 0), (2, 0), 2)),
        ([0, 0, 1, 1, 1, 1], ((1, 0), (0, 0), 0)),
        ([0, 1, 1], ((0, 0), (0, 0), 0)),
        ([0, 1, 0, 0, 0, 0, 0, 0, 1], ((0, 0), (0, 0), 3)),
        (
            [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1],
            ((1, 1), (2, 2), 2),
        ),
        (
            [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1],
            ((1, 1), (1, 3), 2),
        ),
    ],
)
def test_def_without_or_with_nesting_none_any(
    def_without_or_with_nesting_none_any, choices, counts
):
    trail, proposals = trail_expr(def_without_or_with_nesting_none_any), []

    while proposals := get_next_proposals(trail, proposals):
        proposals = [proposals[choices.pop(0)]]

    assert trail.backrefs == {
        k: v
        for k, v in {
            "1": "1"
            + ("2" + "34" * counts[1][0] + "5") * counts[0][0]
            + ("2" + "34" * counts[1][1] + "5") * counts[0][1]
            + "6"
            + "78" * counts[2]
            + "9",
            "2": ("2" + "34" * counts[1][0] + "5") * counts[0][0]
            + ("2" + "34" * counts[1][1] + "5") * counts[0][1],
            "3": "34" * counts[1][0] + "34" * counts[1][1],
            "4": "78" * counts[2],
        }.items()
        if v != ""
    }


@pytest.fixture
def def_with_or_with_nesting_none_any():
    return (
        '(?<1> "1" (?<2> (?<3> "2" (?<4> "3" "4")* "5")* | (?<5> (?<6> "6" "7")* "8")))'
    )


@pytest.mark.parametrize(
    "choices, counts",
    [
        ([0, 2, 0, 0, 0, 1], ((0, 0), (0, 0), 2, (0, 1))),
        ([0, 0, 0, 0, 1, 1], ((1, 0), (1, 0), 0, (1, 0))),
        ([0, 0, 0, 0, 0, 0, 0, 0, 1, 1], ((1, 0), (3, 0), 0, (1, 0))),
        ([0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1], ((1, 1), (3, 1), 0, (1, 0))),
    ],
)
def test_def_with_or_with_nesting_none_any(
    def_with_or_with_nesting_none_any, choices, counts
):
    trail, proposals = trail_expr(def_with_or_with_nesting_none_any), []

    while proposals := get_next_proposals(trail, proposals):
        proposals = [proposals[choices.pop(0)]]

    assert trail.backrefs == {
        k: v
        for k, v in {
            "1": "1"
            + ("2" + "34" * counts[1][0] + "5") * counts[0][0]
            + ("2" + "34" * counts[1][1] + "5") * counts[0][1]
            + "67" * counts[2]
            + "8" * (1 if counts[2] else 0),
            "2": ("2" + "34" * counts[1][0] + "5") * counts[0][0]
            + ("2" + "34" * counts[1][1] + "5") * counts[0][1]
            + "67" * counts[2]
            + "8" * (1 if counts[2] else 0),
            "3": ("2" + "34" * counts[1][0] + "5") * counts[0][0]
            + ("2" + "34" * counts[1][1] + "5") * counts[0][1],
            "4": "34" * counts[1][0] + "34" * counts[1][1],
            "5": "67" * counts[2] + "8" * counts[3][1],
            "6": "67" * counts[2],
        }.items()
        if v != ""
    }


@pytest.fixture
def def_with_or_with_nesting_once_any():
    return (
        '(?<1> "1" (?<2> (?<3> "2" (?<4> "3" "4")+ "5")+ | (?<5> (?<6> "6" "7")+ "8")))'
    )


@pytest.mark.parametrize(
    "choices, counts",
    [
        ([0, 1, 0, 0, 0, 1], ((0, 0), (0, 0), 2, (0, 1))),
        ([0, 0, 0, 0, 1, 1], ((1, 0), (1, 0), 0, (1, 0))),
        ([0, 0, 0, 0, 0, 0, 0, 0, 1, 1], ((1, 0), (3, 0), 0, (1, 0))),
        ([0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1], ((1, 1), (3, 1), 0, (1, 0))),
    ],
)
def test_def_with_or_with_nesting_once_any(
    def_with_or_with_nesting_once_any, choices, counts
):
    trail, proposals = trail_expr(def_with_or_with_nesting_once_any), []

    while proposals := get_next_proposals(trail, proposals):
        proposals = [proposals[choices.pop(0)]]

    assert trail.backrefs == {
        k: v
        for k, v in {
            "1": "1"
            + ("2" + "34" * counts[1][0] + "5") * counts[0][0]
            + ("2" + "34" * counts[1][1] + "5") * counts[0][1]
            + "67" * counts[2]
            + "8" * (1 if counts[2] else 0),
            "2": ("2" + "34" * counts[1][0] + "5") * counts[0][0]
            + ("2" + "34" * counts[1][1] + "5") * counts[0][1]
            + "67" * counts[2]
            + "8" * (1 if counts[2] else 0),
            "3": ("2" + "34" * counts[1][0] + "5") * counts[0][0]
            + ("2" + "34" * counts[1][1] + "5") * counts[0][1],
            "4": "34" * counts[1][0] + "34" * counts[1][1],
            "5": "67" * counts[2] + "8" * counts[3][1],
            "6": "67" * counts[2],
        }.items()
        if v != ""
    }


@pytest.fixture
def def_with_or_with_nesting_once_none():
    return (
        '(?<1> "1" (?<2> (?<3> "2" (?<4> "3" "4")? "5")? | (?<5> (?<6> "6" "7")? "8")))'
    )


@pytest.mark.parametrize(
    "choices, counts",
    [
        ([0, 2, 0, 0, 0, 1], ((0, 0), (0, 0), 1, (0, 1))),
        ([0, 0, 0, 0, 0, 0], ((1, 0), (1, 0), 0, (1, 0))),
    ],
)
def test_def_with_or_with_nesting_once_none(
    def_with_or_with_nesting_once_none, choices, counts
):
    with TrailContext(PARSE_BREFS="1"):
        trail, proposals = trail_expr(def_with_or_with_nesting_once_none), []

        while proposals := get_next_proposals(trail, proposals):
            proposals = [proposals[choices.pop(0)]]

    assert trail.backrefs == {
        k: v
        for k, v in {
            "1": "1"
            + ("2" + "34" * counts[1][0] + "5") * counts[0][0]
            + ("2" + "34" * counts[1][1] + "5") * counts[0][1]
            + "67" * counts[2]
            + "8" * (1 if counts[2] else 0),
            "2": ("2" + "34" * counts[1][0] + "5") * counts[0][0]
            + ("2" + "34" * counts[1][1] + "5") * counts[0][1]
            + "67" * counts[2]
            + "8" * (1 if counts[2] else 0),
            "3": ("2" + "34" * counts[1][0] + "5") * counts[0][0]
            + ("2" + "34" * counts[1][1] + "5") * counts[0][1],
            "4": "34" * counts[1][0] + "34" * counts[1][1],
            "5": "67" * counts[2] + "8" * counts[3][1],
            "6": "67" * counts[2],
        }.items()
        if v != ""
    }
