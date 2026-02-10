from collections import deque
import random
from lark import Lark

from lextrail.assemble import get_next_tokens, asm_cfg


def simulate_response(cfg: str, alphabet: list[str]) -> str:
    asm = asm_cfg(cfg, alphabet)
    response, value = [], ""

    while values := get_next_tokens(asm, value):
        value = random.choice(values)
        response.append(value)

    return "".join(response)


def test_asm_XXXXX01():
    example = r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """

    alphabet = [
        "+",
        "-",
        "*",
        "/",
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
    ]

    response = simulate_response(example, alphabet)

    lark = Lark(
        example,
        parser="lalr",
    )

    assert lark.parse(response)


def test_asm_XXXXX02():
    example = r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor (("*" | "/") factor)*

    factor: NUMBER

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """

    alphabet = [
        "+",
        "-",
        "*",
        "/",
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
    ]

    response = simulate_response(example, alphabet)

    lark = Lark(
        example,
        parser="lalr",
    )

    assert lark.parse(response)


def test_asm_XXXXX03():
    example = r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor (("*" | "/") factor)?

    factor: NUMBER

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """

    alphabet = [
        "+",
        "-",
        "*",
        "/",
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
    ]

    response = simulate_response(example, alphabet)

    lark = Lark(
        example,
        parser="lalr",
    )

    assert lark.parse(response)


def test_asm_XXXXX04():
    example = r"""
    start: expression

    expression: term (("+" | "-") term)*

    term: factor (("*" | "/") factor)?

    factor: NUMBER

    NUMBER: ("0")|("1")|("2")|("3")|("4")|("5")
    """

    alphabet = [
        "+",
        "-",
        "*",
        "/",
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
    ]

    response = simulate_response(example, alphabet)

    lark = Lark(
        example,
        parser="lalr",
    )

    assert lark.parse(response)


def test_asm_XXXXX05():
    example = r"""
    start: expression

    expression: term (("+" | "-") term)

    term: factor (("*" | "/") factor)

    factor: NUMBER

    NUMBER: /[0-5]+\.[0-5]+/
    """

    alphabet = [
        "+",
        "-",
        "*",
        "/",
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        ".",
    ]

    response = simulate_response(example, alphabet)

    lark = Lark(
        example,
        parser="lalr",
    )

    assert lark.parse(response)


def test_asm_MXXXX06():
    example = r"""
    start: L0

    L0: "A" L1

    L1: "C" L2

    L2: "D" L3

    L3: "F"
    """

    asm = asm_cfg(example, ["ACDF"])

    result = get_next_tokens(asm, "")
    correct = ["ACDF"]

    assert set(result) == set(correct)


def test_asm_MPXXX07():
    example = r"""
    start: L0

    L0: ("A" | "B") L1

    L1: "C" L2

    L2: "D" L3

    L3: "F"
    """

    asm = asm_cfg(
        example,
        [
            "A",
            "ACDF",
            "B",
            "BCDF",
            "C",
            "CDF",
        ],
    )

    result = get_next_tokens(asm, "")
    correct = ["A", "B", "BCDF", "ACDF"]

    assert set(result) == set(correct)


def test_asm_MPXXX08():
    example = r"""
    start: L0

    L0: ("A" | "B") L1

    L1: ("C" | "D") L2

    L2: ("E" | "F") L3

    L3: "G"
    """

    asm = asm_cfg(
        example,
        [
            "A",
            "ACEG",
            "B",
            "BDFG",
            "C",
            "CFG",
        ],
    )

    result = get_next_tokens(asm, "")
    correct = ["A", "B", "BDFG", "ACEG"]

    assert set(result) == set(correct)


def test_asm_MPXSL09():
    example = r"""
    start: L0

    L0: ("A" | "B")? L1

    L1: ("C" | "D") L2

    L2: "E" L3*

    L3: "F" "X"
    """

    asm = asm_cfg(
        example,
        [
            "A",
            "ADE",
            "ADEF",
            "B",
            "BDE",
            "BCE",
            "BCEF",
        ],
    )

    result = get_next_tokens(asm, "")
    correct = [
        "A",
        "B",
        "BDE",
        "BCE",
        "BCEF",
        "ADE",
        "ADEF",
    ]

    assert set(result) == set(correct)


def test_asm_MPRSL10():
    example = r"""
    start: L0

    L0: ("A" | "B")+ L1

    L1: ("C" | "D") L2

    L2: "E" L3*

    L3: /FGH/
    """

    asm = asm_cfg(
        example,
        [
            "A",
            "ADE",
            "ADEF",
            "B",
            "BDE",
            "BCE",
            "BCEF",
        ],
    )

    result = get_next_tokens(asm, "")
    correct = [
        "A",
        "B",
        "BDE",
        "BCE",
        "BCEF",
        "ADE",
        "ADEF",
    ]

    assert set(result) == set(correct)


def test_asm_MPRSL11():
    example = r"""
    start: L0

    L0: ("A" | "B")+ L1

    L1: ("C" | "D") L2

    L2: "E" L3*

    L3: /FGH/
    """

    asm = asm_cfg(
        example,
        [
            "AD",
            "EF",
            "GH",
        ],
    )

    alphabet = deque(["AD", "EF", "GH", ""])

    response, value = [], ""
    while response := get_next_tokens(asm, value):
        value, correct = response.pop(), alphabet.popleft()

        assert value == correct
