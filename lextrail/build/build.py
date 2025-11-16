from collections import deque
from dataclasses import dataclass, field
from enum import IntFlag
from os import getenv
from typing import Deque

from lextrail.base import Symbol, Symbol_Kind, SymbolGraph
from lextrail.build.passes import build_symbol_from_lexeme, definition_into_lexeme_queue
from lextrail.helpers import is_end_def_symbol, remove_single_nodes, safe_node_connect


def construct_symbol_graph(lexemes: list[str]):
    symbol_graph = SymbolGraph()

    if not lexemes:
        return symbol_graph

    previous = build_symbol_from_lexeme(lexemes[0])
    symbol_graph.initials = [previous]
    symbol_graph.tree[previous]

    for lexeme in lexemes[1:]:
        next = build_symbol_from_lexeme(lexeme)
        symbol_graph.tree[previous] = [next]
        previous = next

    symbol_graph.finals = [previous]

    return symbol_graph


def connect_symbol_graph(
    symbol_graph_lhs: SymbolGraph,
    symbol_graph_rhs: SymbolGraph,
) -> SymbolGraph:
    if not symbol_graph_lhs.tree and not symbol_graph_rhs.tree:
        return SymbolGraph()

    elif not symbol_graph_lhs.tree:
        return symbol_graph_rhs

    elif not symbol_graph_rhs.tree:
        return symbol_graph_lhs

    symbol_graph_lhs.tree = remove_single_nodes(symbol_graph_lhs.tree)
    symbol_graph_rhs.tree = remove_single_nodes(symbol_graph_rhs.tree)

    symbol_graph_tree_out = symbol_graph_lhs.tree | symbol_graph_rhs.tree

    if int(getenv("SKIP_RULE", 1)):
        end_def_symbols = [
            symbol for symbol in symbol_graph_lhs.finals if is_end_def_symbol(symbol)
        ]

        assert len(end_def_symbols) <= 1, "Duplicate `END` final symbols."

        for end_def_symbol in end_def_symbols:
            predecessors = [
                parent
                for parent, children in symbol_graph_lhs.tree.items()
                if end_def_symbol in children
            ]

            for predecessor in predecessors:
                symbol_graph_lhs.tree[predecessor].remove(end_def_symbol)

            symbol_graph_lhs.finals.remove(end_def_symbol)
            symbol_graph_lhs.finals.extend(predecessors)

        end_def_symbols = [
            symbol for symbol in symbol_graph_lhs.initials if is_end_def_symbol(symbol)
        ]

        assert len(end_def_symbols) <= 1, "Duplicate `END` initial symbols."

        for end_def_symbol in end_def_symbols:
            symbol_graph_lhs.initials.remove(end_def_symbol)
            symbol_graph_lhs.initials += symbol_graph_rhs.initials

    symbol_graph_initials_out, symbol_graph_finals_out = (
        symbol_graph_lhs.initials,
        symbol_graph_rhs.finals,
    )

    for symbol_final in symbol_graph_lhs.finals:
        for symbol_initial in symbol_graph_rhs.initials:
            # [NOTE] Graphs of kind `NONE_ONCE` have their `END_DEF` symbol as initials, if
            # a graph connects them from the left, then the `END_DEF` symbol must be added to the
            # finals.
            # Not only it's a logical implication, but it allows to not lose track of the `END_DEF`
            # symbol for the next connections.
            if (
                is_end_def_symbol(symbol_initial)
                and symbol_initial not in symbol_graph_rhs.finals
            ):
                symbol_graph_rhs.finals.append(symbol_initial)

            safe_node_connect(symbol_graph_tree_out, symbol_final, symbol_initial)

    return SymbolGraph(
        initials=symbol_graph_initials_out,
        tree=symbol_graph_tree_out,
        finals=symbol_graph_finals_out,
    )


def union_symbol_graph(
    symbol_graph_lhs: SymbolGraph,
    symbol_graph_rhs: SymbolGraph,
) -> SymbolGraph:
    if not symbol_graph_lhs.tree and not symbol_graph_rhs.tree:
        return SymbolGraph()

    elif not symbol_graph_lhs.tree:
        return symbol_graph_rhs

    elif not symbol_graph_rhs.tree:
        return symbol_graph_lhs

    symbol_graph_tree_out = symbol_graph_lhs.tree | symbol_graph_rhs.tree

    # Remove duplicate `END` symbols in the initials.
    end_def_symbols_lhs, end_def_symbols_rhs = (
        [symbol for symbol in symbol_graph_lhs.initials if is_end_def_symbol(symbol)],
        [symbol for symbol in symbol_graph_rhs.initials if is_end_def_symbol(symbol)],
    )

    assert (
        len(end_def_symbols_lhs) <= 1 and len(end_def_symbols_rhs) <= 1
    ), f"Duplicate `END` initial symbols {end_def_symbols_lhs} and {end_def_symbols_rhs}."

    if end_def_symbols_lhs and end_def_symbols_rhs:
        symbol_graph_rhs.initials.remove(end_def_symbols_rhs[0])

    # Remove duplicate `END` symbols in the finals.
    end_def_symbols_lhs, end_def_symbols_rhs = (
        [symbol for symbol in symbol_graph_lhs.finals if is_end_def_symbol(symbol)],
        [symbol for symbol in symbol_graph_rhs.finals if is_end_def_symbol(symbol)],
    )

    assert (
        len(end_def_symbols_lhs) <= 1 and len(end_def_symbols_rhs) <= 1
    ), "Duplicate `END` final symbols."

    if end_def_symbols_lhs and end_def_symbols_rhs:
        predecessors = [
            parent
            for parent, children in symbol_graph_rhs.tree.items()
            if end_def_symbols_rhs[0] in children
        ]

        for predecessor in predecessors:
            symbol_graph_tree_out[predecessor].remove(end_def_symbols_rhs[0])
            symbol_graph_tree_out[predecessor].append(end_def_symbols_lhs[0])

        symbol_graph_rhs.finals.remove(end_def_symbols_rhs[0])

    return SymbolGraph(
        initials=symbol_graph_lhs.initials + symbol_graph_rhs.initials,
        tree=symbol_graph_tree_out,
        finals=symbol_graph_lhs.finals + symbol_graph_rhs.finals,
    )


class Delimiter_Property(IntFlag):
    NULL = 0 << 0
    STOP = 1 << 0
    LOOP = 1 << 1
    PIPE = 1 << 2


# [TODO] Tests needs to go over combinations of different types <{}>, <[]>, {<>}, {[]}..
def cast_symbol_graph(symbol_graph: SymbolGraph, kind: Delimiter_Property):
    initials, tree, finals = (
        symbol_graph.initials,
        symbol_graph.tree,
        symbol_graph.finals,
    )

    end_def_symbol = (
        next((s for s in initials if is_end_def_symbol(s)), None)
        or next((s for s in finals if is_end_def_symbol(s)), None)
        or Symbol("END", Symbol_Kind.END)
    )

    if kind & Delimiter_Property.LOOP:
        # Need to re-establish the loop for mixed graphs built through unions.
        finals += (
            [parent for parent, children in tree.items() if end_def_symbol in children]
            if end_def_symbol in finals
            else []
        )

        for final in finals:
            for initial in initials:
                # Nested casts would lead to duplicates.
                safe_node_connect(tree, final, initial)

            safe_node_connect(tree, final, end_def_symbol)

        symbol_graph.finals = [end_def_symbol]

    elif kind & Delimiter_Property.STOP:
        symbol_graph.initials += (
            [end_def_symbol] if end_def_symbol not in initials else []
        )
        tree[end_def_symbol] = []

    return symbol_graph


@dataclass(slots=True)
class Accumulator:
    graph: SymbolGraph = field(default_factory=lambda: SymbolGraph())
    kind: Delimiter_Property = Delimiter_Property.NULL
    tag: str = ""


def build_symbol_graph(symbol_def: str):
    LEXEME_TO_KIND = {
        "(": Delimiter_Property.NULL,
        "{": Delimiter_Property.LOOP,
        "[": Delimiter_Property.STOP,
        "|": Delimiter_Property.PIPE,
    }

    lexemes = definition_into_lexeme_queue(symbol_def)
    state: Deque[Accumulator] = deque([Accumulator()])
    current_accumulated_lexemes: list[str] = []

    while lexemes:
        lexeme = lexemes.popleft()

        if lexeme in "([{|":
            accumulated_graph = construct_symbol_graph(current_accumulated_lexemes)
            state[-1].graph = connect_symbol_graph(state[-1].graph, accumulated_graph)
            current_accumulated_lexemes.clear()

            state.append(Accumulator(SymbolGraph(), LEXEME_TO_KIND[lexeme]))

        elif lexeme.startswith("?<") and lexeme.endswith(">"):
            state[-1].tag = lexeme[2:-1]

        elif lexeme in ")]}":
            accumulated_graph = construct_symbol_graph(current_accumulated_lexemes)
            state[-1].graph = connect_symbol_graph(state[-1].graph, accumulated_graph)
            current_accumulated_lexemes.clear()

            accumulator = state.pop()
            while accumulator.kind == Delimiter_Property.PIPE:
                state[-1].graph = union_symbol_graph(state[-1].graph, accumulator.graph)
                accumulator = state.pop()

            casted = cast_symbol_graph(accumulator.graph, accumulator.kind)

            tag = accumulator.tag
            for symbol in casted.symbols:
                symbol.tags += [tag] if tag else []

            state[-1].graph = connect_symbol_graph(
                state[-1].graph,
                casted,
            )

        else:
            current_accumulated_lexemes.append(lexeme)

    assert len(state) == 1, "Only one consumer should remain."

    return state.pop().graph
