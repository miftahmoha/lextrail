from typing import Any
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, IntFlag
from itertools import chain
from os import getenv
from uuid import UUID, uuid4

from lextrail.parse import split_definition_into_lexemes


class SymbolKind(Enum):
    TERMINAL = 1
    REGEX = 2
    VARIABLE = 3
    REFERENCE = 4
    END = 5


@dataclass(slots=True)
class Symbol:
    content: str
    kind: SymbolKind
    id: UUID = field(default_factory=lambda: uuid4())
    tags: list[str] = field(default_factory=list)

    def __hash__(self):
        return hash(self.id)

    def serialize(self):
        return {
            # `label` is the convention used by Viz.
            "label": self.content,
            "id": str(self.id),
            "kind": str(self.kind),
        }


@dataclass(slots=True)
class SymbolGraph:
    initials: list[Symbol] = field(default_factory=list)
    tree: dict[Symbol, list[Symbol]] = field(default_factory=lambda: defaultdict(list))
    finals: list[Symbol] = field(default_factory=list)

    def __eq__(self, other) -> bool:
        if isinstance(other, SymbolGraph):
            return (
                (self.initials == other.initials)
                and (self.tree == other.tree)
                and (self.finals == other.finals)
            )
        return NotImplemented

    def __bool__(self) -> bool:
        return bool(self.initials) and bool(self.tree) and bool(self.finals)

    @property
    def symbols(self):
        return set(chain(self.initials, *self.tree.values()))

    def serialize(self) -> dict[str, Any]:
        nodes = [symbol.serialize() for symbol in self.symbols]

        edges = [
            {"from": str(symbol.id), "to": str(successor.id), "color": "gray"}
            for symbol, successors in self.tree.items()
            for successor in successors
        ]

        return {"nodes": nodes, "edges": edges}

    def copy(self):
        return SymbolGraph(
            initials=self.initials.copy(),
            tree=self.tree.copy(),
            finals=self.finals.copy(),
        )


def build_symbol_from_lexeme(content: str) -> Symbol:
    if content.startswith('"') and content.endswith('"'):
        node = Symbol(content[1:-1], SymbolKind.TERMINAL)
    elif content.startswith("/") and content.endswith("/"):
        node = Symbol(content[1:-1], SymbolKind.REGEX)
    elif content.startswith("$<") and content.endswith(">"):
        node = Symbol(content[2:-1], SymbolKind.REFERENCE)
    else:
        node = Symbol(content, SymbolKind.VARIABLE)

    return node


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
            symbol
            for symbol in symbol_graph_lhs.finals
            if symbol.kind == SymbolKind.END
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
            symbol
            for symbol in symbol_graph_lhs.initials
            if symbol.kind == SymbolKind.END
        ]

        assert len(end_def_symbols) <= 1, "Duplicate `END` initial symbols."

        for end_def_symbol in end_def_symbols:
            symbol_graph_lhs.initials.remove(end_def_symbol)
            # [TODO] Fix this.
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
                symbol_initial.kind == SymbolKind.END
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
        [
            symbol
            for symbol in symbol_graph_lhs.initials
            if symbol.kind == SymbolKind.END
        ],
        [
            symbol
            for symbol in symbol_graph_rhs.initials
            if symbol.kind == SymbolKind.END
        ],
    )

    assert (
        len(end_def_symbols_lhs) <= 1 and len(end_def_symbols_rhs) <= 1
    ), f"Duplicate `END` initial symbols {end_def_symbols_lhs} and {end_def_symbols_rhs}."

    if end_def_symbols_lhs and end_def_symbols_rhs:
        symbol_graph_rhs.initials.remove(end_def_symbols_rhs[0])

    # Remove duplicate `END` symbols in the finals.
    end_def_symbols_lhs, end_def_symbols_rhs = (
        [symbol for symbol in symbol_graph_lhs.finals if symbol.kind == SymbolKind.END],
        [symbol for symbol in symbol_graph_rhs.finals if symbol.kind == SymbolKind.END],
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


class DelimiterProperty(IntFlag):
    NULL = 0 << 0
    STOP = 1 << 0
    LOOP = 1 << 1
    PIPE = 1 << 2


# [TODO] Tests needs to go over combinations of different types <{}>, <[]>, {<>}, {[]}, etc.
def cast_symbol_graph(symbol_graph: SymbolGraph, kind: DelimiterProperty):
    initials, tree, finals = (
        symbol_graph.initials,
        symbol_graph.tree,
        symbol_graph.finals,
    )

    end_def_symbol = (
        next((s for s in initials if s.kind == SymbolKind.END), None)
        or next((s for s in finals if s.kind == SymbolKind.END), None)
        or Symbol("", SymbolKind.END)
    )

    if kind & DelimiterProperty.LOOP:
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

    elif kind & DelimiterProperty.STOP:
        symbol_graph.initials += (
            [end_def_symbol] if end_def_symbol not in initials else []
        )
        tree[end_def_symbol] = []

    return symbol_graph


@dataclass(slots=True)
class TrailBuilder:
    graph: SymbolGraph = field(default_factory=lambda: SymbolGraph())
    kind: DelimiterProperty = DelimiterProperty.NULL
    tag: str = ""


def build_symbol_graph(symbol_def: str):
    LEXEME_TO_KIND = {
        "(": DelimiterProperty.NULL,
        "{": DelimiterProperty.LOOP,
        "[": DelimiterProperty.STOP,
        "|": DelimiterProperty.PIPE,
    }

    lexemes = split_definition_into_lexemes(symbol_def)
    state: list[TrailBuilder] = [TrailBuilder()]
    accumulated: list[str] = []
    i = 0

    while i < len(lexemes):
        lexeme = lexemes[i]

        if lexeme in "([{|":
            accumulated_graph = construct_symbol_graph(accumulated)
            state[-1].graph = connect_symbol_graph(state[-1].graph, accumulated_graph)
            accumulated.clear()

            state.append(TrailBuilder(SymbolGraph(), LEXEME_TO_KIND[lexeme]))

        elif lexeme.startswith("?<") and lexeme.endswith(">"):
            state[-1].tag = lexeme[2:-1]

        elif lexeme in ")]}":
            accumulated_graph = construct_symbol_graph(accumulated)
            state[-1].graph = connect_symbol_graph(state[-1].graph, accumulated_graph)
            accumulated.clear()

            accumulator = state.pop()
            while accumulator.kind == DelimiterProperty.PIPE:
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
            accumulated.append(lexeme)

        i += 1

    assert len(state) == 1, "Only one builder should remain."

    return state.pop().graph


# ============================ HELPERS ============================


def remove_single_nodes(
    symbol_tree: dict[Symbol, list[Symbol]],
) -> dict[Symbol, list[Symbol]]:
    return defaultdict(list, ((k, v) for k, v in symbol_tree.items() if v))


def safe_node_connect(tree: dict[Symbol, list[Symbol]], from_: Symbol, to_: Symbol):
    tree[from_] += (
        [to_] if to_ not in tree[from_] and from_.kind != SymbolKind.END else []
    )
