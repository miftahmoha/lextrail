from collections import deque

import pytest

from lextrail.guide import trail_exp, get_next_values


def test_reference_XXXXX01():
    example = '(?<1>"1" (?<2> "2" "3") "4" (?<3> "5" "6") "7")'

    trail, value = trail_exp(example), ""

    while values := sorted(
        get_next_values(trail, value), key=lambda x: int(x) if x else 10
    ):
        value = values[0]

    assert trail.state.backrefs == {"1": "1234567", "2": "23", "3": "56"}


def test_reference_SXXXX02():
    example = '(?<1> "1" (?<2> "2" "3" "4") (?<3> "5" "6") "7")'

    trail, value = trail_exp(example), ""

    while values := sorted(
        get_next_values(trail, value), key=lambda x: int(x) if x else 10
    ):
        value = values[0]

    assert trail.state.backrefs == {"1": "1234567", "2": "234", "3": "56"}


def test_reference_XNXXX03():
    example = '(?<1> "1" (?<2> "2" (?<3> "3" "4") "5" (?<4> "6" "7") "8") "9" "10")'

    trail, value = trail_exp(example), ""

    while values := sorted(
        get_next_values(trail, value), key=lambda x: int(x) if x else 10
    ):
        value = values[0]

    assert trail.state.backrefs == {
        "1": "12345678910",
        "2": "2345678",
        "3": "34",
        "4": "67",
    }


def test_reference_SNXXX04():
    example = '(?<1> "1" (?<2> "2" (?<3> "3" "4" "5") (?<4> "6" "7") "8") "9" "10")'

    trail, value = trail_exp(example), ""

    while values := sorted(
        get_next_values(trail, value), key=lambda x: int(x) if x else 10
    ):
        value = values[0]

    assert trail.state.backrefs == {
        "1": "12345678910",
        "2": "2345678",
        "3": "345",
        "4": "67",
    }


def test_reference_XNPXX05():
    example = (
        '(?<1> "1" (?<2> "2" (?<3> "3" "4") "5" | "6" (?<4> "7" "8") "9") "10" "11")'
    )

    trail, value = trail_exp(example), ""

    while values := sorted(
        get_next_values(trail, value), key=lambda x: int(x) if x else 10
    ):
        value = values[0]

    assert trail.state.backrefs == {
        "1": "123451011",
        "2": "2345",
        "3": "34",
    }


def test_reference_SNPXX06():
    example = '(?<1> "1" (?<2> "2" (?<3> "3" "4" "5") | ("6" "7") "8") "9" "10")'

    trail, value = trail_exp(example), ""

    while values := sorted(
        get_next_values(trail, value), key=lambda x: int(x) if x else 10
    ):
        value = values[0]

    assert trail.state.backrefs == {
        "1": "12345910",
        "2": "2345",
        "3": "345",
    }


@pytest.mark.parametrize(
    "choices, counts",
    [
        (deque([0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0]), (3, 2)),
        (deque([0, 0, 0, 1, 1, 0]), (1, 0)),
        (deque([0, 1, 1, 1, 0]), (0, 0)),
        (deque([0, 1, 0, 0, 1, 0]), (0, 1)),
        (deque([0, 0, 0, 1, 0, 0, 1, 0]), (1, 1)),
        (deque([0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0]), (2, 3)),
    ],
)
def test_reference_XXXSL07(choices, counts):
    example = '(?<1> "1" (?<2> "2" "3")* "4" (?<3> "5" "6")* "7")'

    trail, value = trail_exp(example), ""

    while values := sorted(
        get_next_values(trail, value), key=lambda x: int(x) if x else 10
    ):
        value = values[choices.popleft()]

    assert trail.state.backrefs == {
        k: v
        for k, v in {
            "1": "1" + "23" * counts[0] + "4" + "56" * counts[1] + "7",
            "2": "23" * counts[0],
            "3": "56" * counts[1],
        }.items()
        if v != ""
    }


@pytest.mark.parametrize(
    "choices, counts",
    [
        (deque([0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0]), ((1, 0), (2, 0), 2)),
        (deque([0, 0, 1, 1, 1, 1]), ((1, 0), (0, 0), 0)),
        (deque([0, 1, 1]), ((0, 0), (0, 0), 0)),
        (deque([0, 1, 0, 0, 0, 0, 0, 0, 1]), ((0, 0), (0, 0), 3)),
        (
            deque([0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1]),
            ((1, 1), (2, 2), 2),
        ),
        (
            deque([0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1]),
            ((1, 1), (1, 3), 2),
        ),
    ],
)
def test_reference_XNXSL08(choices, counts):
    example = '(?<1> "1" (?<2> "2" (?<3> "3" "4")* "5")* "6" (?<4> "7" "8")* "9")'

    trail, value = trail_exp(example), ""

    while values := sorted(
        get_next_values(trail, value), key=lambda x: int(x) if x else 10
    ):
        value = values[choices.popleft()]

    assert trail.state.backrefs == {
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


@pytest.mark.parametrize(
    "choices, counts",
    [
        (deque([0, 1, 0, 0, 0, 1]), ((0, 0), (0, 0), 2, (0, 1))),
        (deque([0, 0, 0, 0, 1, 1]), ((1, 0), (1, 0), 0, (1, 0))),
        (deque([0, 0, 0, 0, 0, 0, 0, 0, 1, 1]), ((1, 0), (3, 0), 0, (1, 0))),
        (
            deque([0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1]),
            ((1, 1), (3, 1), 0, (1, 0)),
        ),
    ],
)
def test_reference_XNPSL09(choices, counts):
    example = (
        '(?<1> "1" (?<2> (?<3> "2" (?<4> "3" "4")* "5")* | (?<5> (?<6> "6" "7")* "8")))'
    )

    trail, value = trail_exp(example), ""

    while values := sorted(
        get_next_values(trail, value), key=lambda x: int(x) if x else 10
    ):
        value = values[choices.popleft()]

    assert trail.state.backrefs == {
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


@pytest.mark.parametrize(
    "choices, counts",
    [
        (deque([0, 1, 0, 0, 0, 1]), ((0, 0), (0, 0), 2, (0, 1))),
        (deque([0, 0, 0, 0, 1, 1]), ((1, 0), (1, 0), 0, (1, 0))),
        (deque([0, 0, 0, 0, 0, 0, 0, 0, 1, 1]), ((1, 0), (3, 0), 0, (1, 0))),
        (
            deque([0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1]),
            ((1, 1), (3, 1), 0, (1, 0)),
        ),
    ],
)
def test_reference_XNPXL10(choices, counts):
    example = (
        '(?<1> "1" (?<2> (?<3> "2" (?<4> "3" "4")+ "5")+ | (?<5> (?<6> "6" "7")+ "8")))'
    )

    trail, value = trail_exp(example), ""

    while values := sorted(
        get_next_values(trail, value), key=lambda x: int(x) if x else 10
    ):
        value = values[choices.popleft()]

    assert trail.state.backrefs == {
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


@pytest.mark.parametrize(
    "choices, counts",
    [
        (deque([0, 1, 0, 0, 0, 1]), ((0, 0), (0, 0), 1, (0, 1))),
        (deque([0, 0, 0, 0, 0, 0]), ((1, 0), (1, 0), 0, (1, 0))),
    ],
)
def test_reference_XNPXL11(choices, counts):
    example = (
        '(?<1> "1" (?<2> (?<3> "2" (?<4> "3" "4")? "5")? | (?<5> (?<6> "6" "7")? "8")))'
    )

    trail, value = trail_exp(example), ""

    while values := sorted(
        get_next_values(trail, value), key=lambda x: int(x) if x else 10
    ):
        value = values[choices.popleft()]

    assert trail.state.backrefs == {
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
