import pytest

from lextrail.base import Symbol, SymbolGraph
from lextrail.build import (
    build_symbol_graph,
    connect_symbol_graph,
    construct_symbol_graph,
)
from lextrail.helpers import get_ordered_symbols_from_symbol_graph

# ----------------------------- construct_symbol_subgraph -----------------------------


@pytest.fixture
def simple_subdef_without_or():
    return """ "(" expression ")" """


def test_construct_symbol_subgraph_simple_subdef_without_or(
    simple_subdef_without_or: str,
):
    generated_symbol_graph = construct_symbol_graph(simple_subdef_without_or.split())
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def simple_subdef_with_regex():
    return """ /[0-9]*.[0-9]*/ """


def test_construct_symbol_subgraph_simple_subdef_with_regex(
    simple_subdef_with_regex: str,
):
    generated_symbol_graph = construct_symbol_graph(simple_subdef_with_regex.split())
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols["[0-9]*.[0-9]*|0"]]
    tree: dict[Symbol, list[Symbol]] = dict(
        {
            symbols["[0-9]*.[0-9]*|0"]: [],
        },
    )
    finals = [symbols["[0-9]*.[0-9]*|0"]]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# ----------------------------- connect_symbol_graph -----------------------------


def test_connect_symbol_graph_simple_subdefs(
    simple_subdef_without_or: str, simple_subdef_with_regex: str
):
    symbol_graph_lhs, symbol_graph_rhs = construct_symbol_graph(
        simple_subdef_without_or.split()
    ), construct_symbol_graph(simple_subdef_with_regex.split())
    generated_symbol_graph = connect_symbol_graph(symbol_graph_lhs, symbol_graph_rhs)
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [symbols['")"|0']],
            symbols['")"|0']: [symbols["[0-9]*.[0-9]*|0"]],
        },
    )
    finals = [symbols["[0-9]*.[0-9]*|0"]]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)
    assert true_symbol_graph == generated_symbol_graph


def test_connect_symbol_graph_simple_subdefs_with_or(
    simple_subdef_without_or: str, simple_subdef_with_or: str
):
    symbol_graph_lhs, symbol_graph_rhs = build_symbol_graph(
        simple_subdef_with_or
    ), construct_symbol_graph(simple_subdef_without_or.split())
    generated_symbol_graph = connect_symbol_graph(symbol_graph_lhs, symbol_graph_rhs)
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols["factor|0"], symbols["factor|1"]]
    tree = dict(
        {
            symbols["factor|0"]: [symbols['"+"|0']],
            symbols["factor|1"]: [symbols['"-"|0']],
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [symbols['")"|0']],
            symbols['"+"|0']: [symbols['"("|0']],
            symbols['"-"|0']: [symbols['"("|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


def test_connect_symbol_graph_subdefs_with_regex_and_or(
    simple_subdef_with_or: str, subdef_with_regex_and_or: str
):
    symbol_graph_lhs, symbol_graph_rhs = build_symbol_graph(
        simple_subdef_with_or
    ), build_symbol_graph(subdef_with_regex_and_or)
    generated_symbol_graph = connect_symbol_graph(symbol_graph_lhs, symbol_graph_rhs)
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols["factor|0"], symbols["factor|1"]]
    tree = dict(
        {
            symbols["factor|0"]: [symbols['"+"|0']],
            symbols["factor|1"]: [symbols['"-"|0']],
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [symbols['")"|0']],
            symbols['"+"|0']: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"-"|1'],
                symbols['"("|0'],
            ],
            symbols['"-"|0']: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"-"|1'],
                symbols['"("|0'],
            ],
            symbols['"-"|1']: [
                symbols["factor|2"],
            ],
        },
    )
    finals = [
        symbols["[0-9]*.[0-9]*|0"],
        symbols["factor|2"],
        symbols['")"|0'],
    ]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph.tree == generated_symbol_graph.tree


# ----------------------------- build_symbol_graph -----------------------------


@pytest.fixture
def simple_subdef_with_or():
    return """ factor "+" | factor "-" """


def test_construct_symbol_subgraph_simple_subdef_with_or(simple_subdef_with_or: str):
    generated_symbol_graph = build_symbol_graph(simple_subdef_with_or)
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols["factor|0"], symbols["factor|1"]]
    tree = dict(
        {
            symbols["factor|0"]: [symbols['"+"|0']],
            symbols["factor|1"]: [symbols['"-"|0']],
        },
    )
    finals = [symbols['"+"|0'], symbols['"-"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def subdef_with_regex_and_or():
    return """ /[0-9]*.[0-9]*/ | "-" factor |  "(" expression ")" """


def test_construct_symbol_subgraph_subdef_with_regex_and_or(
    subdef_with_regex_and_or: str,
):
    generated_symbol_graph = build_symbol_graph(subdef_with_regex_and_or)
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [
        symbols["[0-9]*.[0-9]*|0"],
        symbols['"-"|0'],
        symbols['"("|0'],
    ]

    tree: dict[Symbol, list[Symbol]] = dict(
        {
            symbols["[0-9]*.[0-9]*|0"]: [],
            symbols['"-"|0']: [symbols["factor|0"]],
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [symbols['")"|0']],
        },
    )
    finals = [
        symbols["[0-9]*.[0-9]*|0"],
        symbols["factor|0"],
        symbols['")"|0'],
    ]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# -------- SymbolGraphType.STANDARD --------


@pytest.fixture
def def_without_or_without_special_delimiters():
    return """ "(" expression (factor "-" /[0-9]*.[0-9]*/) ")" """


def test_build_graph_def_without_or_without_special_delimiters(
    def_without_or_without_special_delimiters: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_without_or_without_special_delimiters
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [symbols["factor|0"]],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols["[0-9]*.[0-9]*|0"]],
            symbols["[0-9]*.[0-9]*|0"]: [symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_without_or_seq_without_special_delimiters():
    return """ "(" expression (factor "-" /[0-9]*.[0-9]*/ (power "+") (factor "*") ("/" number) power) ")" """


def test_build_graph_def_without_or_seq_without_special_delimiters(
    def_without_or_seq_without_special_delimiters: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_without_or_seq_without_special_delimiters
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [symbols["factor|0"]],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols["[0-9]*.[0-9]*|0"]],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["power|0"]],
            symbols["power|0"]: [symbols['"+"|0']],
            symbols['"+"|0']: [symbols["factor|1"]],
            symbols["factor|1"]: [symbols['"*"|0']],
            symbols['"*"|0']: [symbols['"/"|0']],
            symbols['"/"|0']: [symbols["number|0"]],
            symbols["number|0"]: [symbols["power|1"]],
            symbols["power|1"]: [symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_without_or_seq_disrupt_in_between_and_end_without_special_delimiters():
    return """ "(" expression (factor "-" (power "+") (factor "*") ("/" number) power ("/" /[0-9]*.[0-9]*/) (factor "+") expression) ")" """


def test_build_graph_def_without_or_seq_disrupt_in_between_and_end_without_special_delimiters(
    def_without_or_seq_disrupt_in_between_and_end_without_special_delimiters: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_without_or_seq_disrupt_in_between_and_end_without_special_delimiters
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [symbols["factor|0"]],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols["power|0"]],
            symbols["power|0"]: [symbols['"+"|0']],
            symbols['"+"|0']: [symbols["factor|1"]],
            symbols["factor|1"]: [symbols['"*"|0']],
            symbols['"*"|0']: [symbols['"/"|0']],
            symbols['"/"|0']: [symbols["number|0"]],
            symbols["number|0"]: [symbols["power|1"]],
            symbols["power|1"]: [symbols['"/"|1']],
            symbols['"/"|1']: [symbols["[0-9]*.[0-9]*|0"]],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|2"]],
            symbols["factor|2"]: [symbols['"+"|1']],
            symbols['"+"|1']: [symbols["expression|1"]],
            symbols["expression|1"]: [symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_out_or_without_special_delimiters():
    return """ "(" expression ((factor "-") | /[0-9]*.[0-9]*/) ")" """


def test_build_graph_def_with_out_or_without_special_delimiters(
    def_with_out_or_without_special_delimiters: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_out_or_without_special_delimiters
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [symbols["factor|0"], symbols["[0-9]*.[0-9]*|0"]],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols['")"|0']],
            symbols["[0-9]*.[0-9]*|0"]: [symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_out_or_ext_without_special_delimiters():
    return """ "(" expression ((factor "-") | /[0-9]*.[0-9]*/ "+" factor) ")" """


def test_build_graph_def_with_out_or_ext_without_special_delimiters(
    def_with_out_or_ext_without_special_delimiters: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_out_or_ext_without_special_delimiters
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [symbols["factor|0"], symbols["[0-9]*.[0-9]*|0"]],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols['")"|0']],
            symbols["[0-9]*.[0-9]*|0"]: [symbols['"+"|0']],
            symbols['"+"|0']: [symbols["factor|1"]],
            symbols["factor|1"]: [symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_or_without_special_delimiters():
    return """ "(" expression ((factor "-") | (/[0-9]*.[0-9]*/ | "+")) ")" """


def test_build_graph_def_with_in_and_out_or_without_special_delimiters(
    def_with_in_and_out_or_without_special_delimiters: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_or_without_special_delimiters
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols['")"|0']],
            symbols["[0-9]*.[0-9]*|0"]: [symbols['")"|0']],
            symbols['"+"|0']: [symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_without_special_delimiters():
    return """ "(" expression ((factor "-") | (/[0-9]*.[0-9]*/ factor | "+" expression)) ")" """


def test_build_graph_def_with_in_and_out_ext_or_without_special_delimiters(
    def_with_in_and_out_ext_or_without_special_delimiters: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_without_special_delimiters
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols['")"|0']],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|1"]],
            symbols["factor|1"]: [symbols['")"|0']],
            symbols['"+"|0']: [symbols["expression|1"]],
            symbols["expression|1"]: [symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# -------- SymbolGraphType.NONE_ANY --------


@pytest.fixture
def def_without_or_with_special_delimiters_none_any():
    return """ "(" expression (factor "-" /[0-9]*.[0-9]*/)* ")" """


def test_build_graph_def_with_or_with_special_delimiters_none_any(
    def_without_or_with_special_delimiters_none_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_without_or_with_special_delimiters_none_any
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)
    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [symbols["factor|0"], symbols['")"|0']],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols["[0-9]*.[0-9]*|0"]],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|0"], symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# -------- SymbolGraphType.STANDARD + SymbolGraphType.NONE_ANY --------


@pytest.fixture
def def_with_out_or_with_special_delimiters_none_any():
    return """ "(" expression ((factor "-")* | /[0-9]*.[0-9]*/) ")" """


def test_build_graph_def_with_out_or_with_special_delimiters(
    def_with_out_or_with_special_delimiters_none_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_out_or_with_special_delimiters_none_any
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['")"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols["factor|0"], symbols['")"|0']],
            symbols["[0-9]*.[0-9]*|0"]: [symbols['")"|0']],
        },
    )

    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph.tree == generated_symbol_graph.tree


@pytest.fixture
def def_with_in_and_out_or_with_special_delimiters_none_any():
    return """ "(" expression ((factor "-")* | (/[0-9]*.[0-9]*/ | "+")*) ")" """


def test_build_graph_def_with_in_and_out_or_with_special_delimiters_none_any(
    def_with_in_and_out_or_with_special_delimiters_none_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_or_with_special_delimiters_none_any
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols["factor|0"], symbols['")"|0']],
            symbols["[0-9]*.[0-9]*|0"]: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols['"+"|0']: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_with_special_delimiters_none_any():
    return """ "(" expression ((factor "-") | (/[0-9]*.[0-9]*/ factor | "+" expression)*)* ")" """


def test_build_graph_def_with_in_and_out_ext_or_with_special_delimiters_none_any(
    def_with_in_and_out_ext_or_with_special_delimiters_none_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_with_special_delimiters_none_any
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|1"]],
            symbols["factor|1"]: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols["factor|0"],
                symbols['")"|0'],
            ],
            symbols['"+"|0']: [symbols["expression|1"]],
            symbols["expression|1"]: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols["factor|0"],
                symbols['")"|0'],
            ],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph.tree == generated_symbol_graph.tree


@pytest.fixture
def def_with_in_and_out_ext_or_seq_with_special_delimiters_none_any():
    return """ "(" expression ((factor "-") ("+" power) | (/[0-9]*.[0-9]*/ factor | "+" expression)*)* ")" """


def test_build_graph_def_with_in_and_out_ext_or_seq_with_special_delimiters_none_any(
    def_with_in_and_out_ext_or_seq_with_special_delimiters_none_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_with_special_delimiters_none_any
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols['"+"|1']],
            symbols['"+"|1']: [symbols["power|0"]],
            symbols["power|0"]: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|1"]],
            symbols["factor|1"]: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols["factor|0"],
                symbols['")"|0'],
            ],
            symbols['"+"|0']: [symbols["expression|1"]],
            symbols["expression|1"]: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols["factor|0"],
                symbols['")"|0'],
            ],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_with_special_delimiters_none_any():
    return """ "(" expression ((factor "-")* ("+" power) | (/[0-9]*.[0-9]*/ factor | "+" expression)*)* ")" """


def test_build_graph_def_with_in_and_out_ext_or_seq_mixed_with_special_delimiters_none_any(
    def_with_in_and_out_ext_or_seq_mixed_with_special_delimiters_none_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_mixed_with_special_delimiters_none_any
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols['"+"|0'],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|1'],
                symbols['")"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols["factor|0"], symbols['"+"|0']],
            symbols['"+"|0']: [symbols["power|0"]],
            symbols["power|0"]: [
                symbols["factor|0"],
                symbols['"+"|0'],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|1'],
                symbols['")"|0'],
            ],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|1"]],
            symbols["factor|1"]: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|1'],
                symbols["factor|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols['"+"|1']: [symbols["expression|1"]],
            symbols["expression|1"]: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|1'],
                symbols["factor|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_any():
    return """ "(" expression ((factor "-")* ("/" factor) ("+" power) expression | (/[0-9]*.[0-9]*/ factor | "+" expression)*)* ")" """


def test_build_graph_def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_any(
    def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_any
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols['"/"|0'],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols["factor|0"], symbols['"/"|0']],
            symbols['"/"|0']: [symbols["factor|1"]],
            symbols["factor|1"]: [symbols['"+"|1']],
            symbols['"+"|1']: [symbols["power|0"]],
            symbols["power|0"]: [symbols["expression|2"]],
            symbols["expression|2"]: [
                symbols["factor|0"],
                symbols['"/"|0'],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|2"]],
            symbols["factor|2"]: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols["factor|0"],
                symbols['"/"|0'],
                symbols['")"|0'],
            ],
            symbols['"+"|0']: [symbols["expression|1"]],
            symbols["expression|1"]: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols["factor|0"],
                symbols['"/"|0'],
                symbols['")"|0'],
            ],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any():
    return """ "(" expression ((factor "-")* ("/" factor) ("+" power)* expression (/[0-9]*.[0-9]*/ "*") | (/[0-9]*.[0-9]*/ factor | "+" expression)*)* ")" """


def test_build_graph_def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any(
    def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols['"/"|0'],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols["factor|0"], symbols['"/"|0']],
            symbols['"/"|0']: [symbols["factor|1"]],
            symbols["factor|1"]: [symbols['"+"|1'], symbols["expression|2"]],
            symbols['"+"|1']: [symbols["power|0"]],
            symbols["power|0"]: [symbols['"+"|1'], symbols["expression|2"]],
            symbols["expression|2"]: [symbols["[0-9]*.[0-9]*|1"]],
            symbols["[0-9]*.[0-9]*|1"]: [symbols['"*"|0']],
            symbols['"*"|0']: [
                symbols["factor|0"],
                symbols['"/"|0'],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|2"]],
            symbols["factor|2"]: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols["factor|0"],
                symbols['"/"|0'],
                symbols['")"|0'],
            ],
            symbols['"+"|0']: [symbols["expression|1"]],
            symbols["expression|1"]: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols["factor|0"],
                symbols['"/"|0'],
                symbols['")"|0'],
            ],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# -------- SymbolGraphType.ONCE_ANY --------


@pytest.fixture
def def_without_or_with_special_delimiters_once_any():
    return """ "(" expression (factor "-" /[0-9]*.[0-9]*/)+ ")" """


def test_build_graph_def_without_or_with_special_delimiters_once_any(
    def_without_or_with_special_delimiters_once_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_without_or_with_special_delimiters_once_any
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [symbols["factor|0"]],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols["[0-9]*.[0-9]*|0"]],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|0"], symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# -------- SymbolGraphType.STANDARD + SymbolGraphType.ONCE_ANY --------


@pytest.fixture
def def_with_in_and_out_or_with_special_delimiters_once_any():
    return """ "(" expression ((factor "-")+ | (/[0-9]*.[0-9]*/ | "+")+) ")" """


def test_build_graph_def_with_in_and_out_or_with_special_delimiters_once_any(
    def_with_in_and_out_or_with_special_delimiters_once_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_or_with_special_delimiters_once_any
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols["factor|0"], symbols['")"|0']],
            symbols["[0-9]*.[0-9]*|0"]: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols['"+"|0']: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_once_any():
    return """ "(" expression ((factor "-")+ ("/" factor) ("+" power)+ expression (/[0-9]*.[0-9]*/ "*") | (/[0-9]*.[0-9]*/ factor | "+" expression)+)+ ")" """


def test_build_graph_def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_once_any(
    def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_once_any: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_once_any
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols["factor|0"], symbols['"/"|0']],
            symbols['"/"|0']: [symbols["factor|2"]],
            symbols["factor|2"]: [symbols['"+"|1']],
            symbols['"+"|1']: [symbols["power|0"]],
            symbols["power|0"]: [symbols['"+"|1'], symbols["expression|2"]],
            symbols["expression|2"]: [symbols["[0-9]*.[0-9]*|1"]],
            symbols["[0-9]*.[0-9]*|1"]: [symbols['"*"|0']],
            symbols['"*"|0']: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|1"]],
            symbols["factor|1"]: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols["factor|0"],
                symbols['")"|0'],
            ],
            symbols['"+"|0']: [symbols["expression|1"]],
            symbols["expression|1"]: [
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols["factor|0"],
                symbols['")"|0'],
            ],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph.tree == generated_symbol_graph.tree


# -------- SymbolGraphType.NONE_ONCE --------


@pytest.fixture
def def_without_or_with_special_delimiters_none_once():
    return """ "(" expression (factor "-" /[0-9]*.[0-9]*/)? ")" """


def test_build_graph_def_without_or_with_special_delimiters_none_once(
    def_without_or_with_special_delimiters_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_without_or_with_special_delimiters_none_once
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [symbols["factor|0"], symbols['")"|0']],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols["[0-9]*.[0-9]*|0"]],
            symbols["[0-9]*.[0-9]*|0"]: [symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# -------- SymbolGraphType.STANDARD + SymbolGraphType.NONE_ONCE --------


@pytest.fixture
def def_with_out_or_with_special_delimiters_none_once():
    return """ "(" expression ((factor "-")? | /[0-9]*.[0-9]*/) ")" """


# [NOTE] There'll be no forcing into `/[0-9]*.[0-9]*/` if none of `[factor "-"]` is chosen which is coherent.
def test_build_graph_def_with_out_or_with_special_delimiters_none_once(
    def_with_out_or_with_special_delimiters_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_out_or_with_special_delimiters_none_once
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['")"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols['")"|0']],
            symbols["[0-9]*.[0-9]*|0"]: [symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_or_with_special_delimiters_none_once():
    return """ "(" expression ((factor "-")? | (/[0-9]*.[0-9]*/ | "+")?) ")" """


def test_build_graph_def_with_in_and_out_or_with_special_delimiters_none_once(
    def_with_in_and_out_or_with_special_delimiters_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_or_with_special_delimiters_none_once
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols['")"|0']],
            symbols["[0-9]*.[0-9]*|0"]: [symbols['")"|0']],
            symbols['"+"|0']: [symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_with_special_delimiters_none_once():
    return """ "(" expression ((factor "-") | (/[0-9]*.[0-9]*/ factor | "+" expression)?)? ")" """


def test_build_graph_def_with_in_and_out_ext_or_with_special_delimiters_none_once(
    def_with_in_and_out_ext_or_with_special_delimiters_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_with_special_delimiters_none_once
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols['")"|0']],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|1"]],
            symbols["factor|1"]: [symbols['")"|0']],
            symbols['"+"|0']: [symbols["expression|1"]],
            symbols["expression|1"]: [symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_seq_with_special_delimiters_none_once():
    return """ "(" expression ((factor "-") ("+" power) | (/[0-9]*.[0-9]*/ factor | "+" expression)?)? ")" """


def test_build_graph_def_with_in_and_out_ext_or_seq_with_special_delimiters_none_once(
    def_with_in_and_out_ext_or_seq_with_special_delimiters_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_with_special_delimiters_none_once
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols['"+"|1']],
            symbols['"+"|1']: [symbols["power|0"]],
            symbols["power|0"]: [symbols['")"|0']],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|1"]],
            symbols["factor|1"]: [symbols['")"|0']],
            symbols['"+"|0']: [symbols["expression|1"]],
            symbols["expression|1"]: [symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_with_special_delimiters_none_once():
    return """ "(" expression ((factor "-")? ("+" power) | (/[0-9]*.[0-9]*/ factor | "+" expression)?)? ")" """


def test_build_graph_def_with_in_and_out_ext_or_seq_mixed_with_special_delimiters_none_once(
    def_with_in_and_out_ext_or_seq_mixed_with_special_delimiters_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_mixed_with_special_delimiters_none_once
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols['"+"|0'],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|1'],
                symbols['")"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols['"+"|0']],
            symbols['"+"|0']: [symbols["power|0"]],
            symbols["power|0"]: [symbols['")"|0']],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|1"]],
            symbols["factor|1"]: [symbols['")"|0']],
            symbols['"+"|1']: [symbols["expression|1"]],
            symbols["expression|1"]: [symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_once():
    return """ "(" expression ((factor "-")? ("/" factor) ("+" power) expression | (/[0-9]*.[0-9]*/ factor | "+" expression)?)? ")" """


def test_build_graph_def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_once(
    def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_mixed_disrupt_end_with_special_delimiters_none_once
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols['"/"|0'],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols['"/"|0']],
            symbols['"/"|0']: [symbols["factor|1"]],
            symbols["factor|1"]: [symbols['"+"|1']],
            symbols['"+"|1']: [symbols["power|0"]],
            symbols["power|0"]: [symbols["expression|2"]],
            symbols["expression|2"]: [symbols['")"|0']],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|2"]],
            symbols["factor|2"]: [symbols['")"|0']],
            symbols['"+"|0']: [symbols["expression|1"]],
            symbols["expression|1"]: [symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_once():
    return """ "(" expression ((factor "-")? ("/" factor) ("+" power)? expression (/[0-9]*.[0-9]*/ "*") | (/[0-9]*.[0-9]*/ factor | "+" expression)?)? ")" """


def test_build_graph_def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_once(
    def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_once
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols['"/"|0'],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols['"/"|0']],
            symbols['"/"|0']: [symbols["factor|1"]],
            symbols["factor|1"]: [symbols['"+"|1'], symbols["expression|2"]],
            symbols['"+"|1']: [symbols["power|0"]],
            symbols["power|0"]: [symbols["expression|2"]],
            symbols["expression|2"]: [symbols["[0-9]*.[0-9]*|1"]],
            symbols["[0-9]*.[0-9]*|1"]: [symbols['"*"|0']],
            symbols['"*"|0']: [symbols['")"|0']],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|2"]],
            symbols["factor|2"]: [symbols['")"|0']],
            symbols['"+"|0']: [symbols["expression|1"]],
            symbols["expression|1"]: [symbols['")"|0']],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# -------- SymbolGraphType.STANDARD + SymbolGraphType.NONE_ANY + SymbolGraphType.NONE_ONCE --------


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any_once():
    return """ "(" expression ((factor "-")* ("/" factor) ("+" power)? expression (/[0-9]*.[0-9]*/ "*") | (/[0-9]*.[0-9]*/ factor | "+" expression)?)* ")" """


def test_build_graph_def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any_once(
    def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any_once
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols['"/"|0'],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols["factor|0"], symbols['"/"|0']],
            symbols['"/"|0']: [symbols["factor|1"]],
            symbols["factor|1"]: [symbols['"+"|1'], symbols["expression|2"]],
            symbols['"+"|1']: [symbols["power|0"]],
            symbols["power|0"]: [symbols["expression|2"]],
            symbols["expression|2"]: [symbols["[0-9]*.[0-9]*|1"]],
            symbols["[0-9]*.[0-9]*|1"]: [symbols['"*"|0']],
            symbols['"*"|0']: [
                symbols["factor|0"],
                symbols['"/"|0'],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|2"]],
            symbols["factor|2"]: [
                symbols["factor|0"],
                symbols['"/"|0'],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols['"+"|0']: [symbols["expression|1"]],
            symbols["expression|1"]: [
                symbols["factor|0"],
                symbols['"/"|0'],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph


# -------- SymbolGraphType.STANDARD + SymbolGraphType.NONE_ANY + SymbolGraphType.ONCE_ANY + SymbolGraphType.NONE_ONCE --------


@pytest.fixture
def def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_once_any_none_once():
    return """ "(" expression ((factor "-")+ ("/" factor) ("+" power)? expression (/[0-9]*.[0-9]*/ "*") | (/[0-9]*.[0-9]*/ factor | "+" expression)?)* ")" """


def test_build_graph_def_with_in_and_otest_build_graph_def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_any_onceut_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_none_once_any_none_once(
    def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_once_any_none_once: str,
):
    generated_symbol_graph = build_symbol_graph(
        def_with_in_and_out_ext_or_seq_mixed_disrupt_in_between_and_end_with_special_delimiters_none_once_any_none_once
    )
    symbols = get_ordered_symbols_from_symbol_graph(generated_symbol_graph)

    initials = [symbols['"("|0']]
    tree = dict(
        {
            symbols['"("|0']: [symbols["expression|0"]],
            symbols["expression|0"]: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["factor|0"]: [symbols['"-"|0']],
            symbols['"-"|0']: [symbols["factor|0"], symbols['"/"|0']],
            symbols['"/"|0']: [symbols["factor|2"]],
            symbols["factor|2"]: [symbols['"+"|1'], symbols["expression|2"]],
            symbols['"+"|1']: [symbols["power|0"]],
            symbols["power|0"]: [symbols["expression|2"]],
            symbols["expression|2"]: [symbols["[0-9]*.[0-9]*|1"]],
            symbols["[0-9]*.[0-9]*|1"]: [symbols['"*"|0']],
            symbols['"*"|0']: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols["[0-9]*.[0-9]*|0"]: [symbols["factor|1"]],
            symbols["factor|1"]: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
            symbols['"+"|0']: [symbols["expression|1"]],
            symbols["expression|1"]: [
                symbols["factor|0"],
                symbols["[0-9]*.[0-9]*|0"],
                symbols['"+"|0'],
                symbols['")"|0'],
            ],
        },
    )
    finals = [symbols['")"|0']]

    true_symbol_graph = SymbolGraph(initials=initials, tree=tree, finals=finals)

    assert true_symbol_graph == generated_symbol_graph
