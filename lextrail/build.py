from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, IntFlag
from itertools import chain
from os import getenv
from typing import Any, Optional
from uuid import UUID, uuid4

from lextrail.helpers import TrailError, format_error
from lextrail.regex import re_parse


class MarkerKind(Enum):
    EMPTY = 0
    GROUP = 1
    QUOTE = 2
    SLASH = 3


@dataclass
class SplitMarker:
    index: int = 0
    kind: MarkerKind = MarkerKind.EMPTY


def split_definition_into_lexemes(definition: str) -> list[str]:
    DELIMITERS = set("()[]{}|")
    QUANTIFIERS = {
        "?": (["["], ["]"]),
        "+": (["{"], ["}"]),
        "*": (["{", "["], ["]", "}"]),
    }

    lexemes: list[str] = []
    in_quote = False
    in_regex = False
    markers: list[SplitMarker] = []
    lexeme: list[str] = []
    i = 0

    def consume_lexeme():
        if lexeme:
            lexemes.append("".join(lexeme))
            lexeme.clear()

    def is_escaped(pos):
        count = 0
        pos -= 1
        while pos >= 0 and definition[pos] == "\\":
            count += 1
            pos -= 1
        return count % 2 == 1

    def peek(offset):
        return definition[i + offset] if 0 <= i + offset < len(definition) else None

    while i < len(definition):
        curr = definition[i]

        # === REGEX ===
        if curr == "/" and not in_quote:
            if not in_regex:
                consume_lexeme()
                lexeme.append(curr)

                markers.append(SplitMarker(index=i, kind=MarkerKind.SLASH))
                in_regex = True
            elif not is_escaped(i):
                lexeme.append(curr)

                result = re_parse(lexeme[1:-1])
                lexeme.clear()
                lexemes.extend(result)

                kind = markers[-1].kind if markers else None
                assert (
                    kind == MarkerKind.SLASH
                ), f"Expected a `MarkerKind.SLASH` marker, found `{kind}`"

                markers.pop()
                in_regex = False

        # === PIPE (OR) OPERATOR ===
        elif curr == "|" and not in_quote and not in_regex:
            consume_lexeme()
            lexemes.append(curr)

        # === QUOTE ===
        elif curr == '"' and not in_regex:
            if not in_quote:
                consume_lexeme()
                lexeme.append(curr)

                markers.append(SplitMarker(index=i, kind=MarkerKind.QUOTE))
                in_quote = True
            elif is_escaped(i):
                lexeme.pop()
                lexeme.append(curr)
            else:
                lexeme.append(curr)
                consume_lexeme()

                kind = markers[-1].kind if markers else None
                assert (
                    kind == MarkerKind.QUOTE
                ), f"Expected a `MarkerKind.QUOTE` marker, found `{kind}`"

                markers.pop()
                in_quote = False

        # === QUANTIFIER ===
        elif curr in QUANTIFIERS and not in_quote and not in_regex:
            prev = peek(-1)

            if prev == ")":
                open_br, close_br = QUANTIFIERS[curr]

                # [TODO] Pop could result in some runtime errors.
                assembled, depth = [], -1
                while (last := lexemes.pop()) != "(" or depth != 0:
                    assembled.append(last)
                    depth += 1 if last == ")" else -1 if last == "(" else 0

                assembled.append(last)

                lexemes += open_br + assembled[::-1] + close_br
            elif prev == "(":
                lexeme.append(curr)
            elif prev == "":
                lexemes.append(curr)
            else:
                # Wrap previous symbol in brackets.
                symbol = (
                    "".join(lexeme) if lexeme else lexemes.pop()
                )  # Accumulated, not yet consumed lexeme, or consumed `/.../` or `"..."`.
                lexeme.clear()
                open_br, close_br = QUANTIFIERS[curr]
                lexemes += open_br + [symbol] + close_br

        # === DELIMITERS ===
        elif curr in DELIMITERS and not in_quote and not in_regex:
            consume_lexeme()
            lexemes.append(curr)

            match curr:
                case "(":
                    markers.append(SplitMarker(index=i, kind=MarkerKind.GROUP))
                case ")":
                    marker = markers.pop() if markers else SplitMarker()

                    if marker.kind != MarkerKind.GROUP:
                        context = definition[:i]

                        raise TrailError(
                            format_error(
                                "Unexpected `)` - no matching opening parenthesis.",
                                context,
                                ")",
                            )
                        )
                case "|":
                    pass
                case _:
                    context = definition[:i]

                    raise TrailError(
                        format_error(
                            "Delimiter reserved for internal use.",
                            context,
                            curr,
                        )
                    )

        # === REFERENCES ===
        elif curr == "<" and not in_quote and not in_regex:
            if peek(-1) == "$" or (peek(-1) == "?" and peek(-2) == "("):
                k = 0
                while (next := peek(k)) != ">":
                    lexeme.append(next)
                    k += 1

                lexeme.append(next)
                consume_lexeme()
                i += k + 1
                continue
            else:
                lexeme.append(curr)

        # === WHITESPACE ===
        elif curr.isspace():
            if in_quote or in_regex:
                lexeme.append(curr)
            else:
                consume_lexeme()

        # === REGULAR CHARACTERS ===
        else:
            lexeme.append(curr)

        i += 1

    consume_lexeme()

    marker = markers.pop() if markers else SplitMarker()

    match marker.kind:
        case MarkerKind.SLASH:
            raise TrailError(
                format_error(
                    "Unterminated regex pattern starting with `/` - add closing delimiter or escape `/` as `\\/`.",
                    definition[: marker.index],
                    "/",
                )
            )
        case MarkerKind.GROUP:
            raise TrailError(
                format_error(
                    "Unmatched '(' - expected a closing ')'.",
                    definition[: marker.index],
                    "(",
                )
            )
        case MarkerKind.QUOTE:
            raise TrailError(
                format_error(
                    'Unclosed string literal - missing " to terminate the string.',
                    definition[: marker.index],
                    '"',
                )
            )

    return ["("] + lexemes + [")"]


class SymbolKind(Enum):
    TERMINAL = 1
    VARIABLE = 2
    REFERENCE = 3
    END = 4


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
    heads: set[Symbol]
    edges: dict[Symbol, set[Symbol]]
    tails: set[Symbol]

    @property
    def symbols(self):
        return set(chain(self.heads, *self.edges.values()))

    @classmethod
    def new(cls):
        return SymbolGraph(heads=set(), edges=defaultdict(set), tails=set())

    def serialize(self) -> dict[str, Any]:
        nodes = [symbol.serialize() for symbol in self.symbols]
        edges = [
            {"from": str(symbol.id), "to": str(successor.id), "color": "gray"}
            for symbol, successors in self.edges.items()
            for successor in successors
        ]

        return {"nodes": nodes, "edges": edges}


def build_symbol_from_lexeme(content: str) -> Symbol:
    if content.startswith('"') and content.endswith('"'):
        node = Symbol(content[1:-1], SymbolKind.TERMINAL)
    elif content.startswith("$<") and content.endswith(">"):
        node = Symbol(content[2:-1], SymbolKind.REFERENCE)
    else:
        node = Symbol(content, SymbolKind.VARIABLE)

    return node


def construct_symbol_graph(lexemes: list[str]):
    graph = SymbolGraph.new()

    if not lexemes:
        return graph

    previous = build_symbol_from_lexeme(lexemes[0])
    graph.heads = {previous}
    graph.edges[previous]

    for lexeme in lexemes[1:]:
        next = build_symbol_from_lexeme(lexeme)
        graph.edges[previous] = {next}
        previous = next

    graph.tails = {previous}

    return graph


def connect_symbol_graph(
    graph_lt: SymbolGraph,
    graph_rt: SymbolGraph,
) -> SymbolGraph:
    if not graph_lt.edges and not graph_rt.edges:
        return SymbolGraph.new()

    elif not graph_lt.edges:
        return graph_rt

    elif not graph_rt.edges:
        return graph_lt

    # Remove standalone nodes.
    graph_lt.edges = defaultdict(set, ((k, v) for k, v in graph_lt.edges.items() if v))
    graph_rt.edges = defaultdict(set, ((k, v) for k, v in graph_rt.edges.items() if v))

    edges = graph_lt.edges | graph_rt.edges

    if int(getenv("SKIP_RULE", 1)):
        end_def_symbols = [
            symbol for symbol in graph_lt.tails if symbol.kind == SymbolKind.END
        ]

        assert len(end_def_symbols) <= 1, "Duplicate `END` final symbols."

        for end_def_symbol in end_def_symbols:
            predecessors = {
                parent
                for parent, children in graph_lt.edges.items()
                if end_def_symbol in children
            }

            for predecessor in predecessors:
                graph_lt.edges[predecessor].remove(end_def_symbol)

            graph_lt.tails.remove(end_def_symbol)
            graph_lt.tails.update(predecessors)

        end_def_symbols = [
            symbol for symbol in graph_lt.heads if symbol.kind == SymbolKind.END
        ]

        assert len(end_def_symbols) <= 1, "Duplicate `END` initial symbols."

        for end_def_symbol in end_def_symbols:
            graph_lt.heads.remove(end_def_symbol)
            graph_lt.heads.update(graph_rt.heads)

    heads, tails = (
        graph_lt.heads,
        graph_rt.tails,
    )

    for symbol_final in graph_lt.tails:
        for symbol_initial in graph_rt.heads:
            # [NOTE] Graphs of kind `NONE_ONCE` have their `END_DEF` symbol as initials, if
            # a graph connects them from the left, then the `END_DEF` symbol must be added to the
            # finals.
            # Not only it's a logical implication, but it allows to not lose track of the `END_DEF`
            # symbol for the next connections.
            if (
                symbol_initial.kind == SymbolKind.END
                and symbol_initial not in graph_rt.tails
            ):
                graph_rt.tails.add(symbol_initial)

            if symbol_final.kind != SymbolKind.END:
                edges[symbol_final].add(symbol_initial)

    return SymbolGraph(
        heads=heads,
        edges=edges,
        tails=tails,
    )


def union_symbol_graph(
    graph_lt: SymbolGraph,
    graph_rt: SymbolGraph,
) -> SymbolGraph:
    if not graph_lt.edges and not graph_rt.edges:
        return SymbolGraph.new()

    elif not graph_lt.edges:
        return graph_rt

    elif not graph_rt.edges:
        return graph_lt

    edges = graph_lt.edges | graph_rt.edges

    # Remove duplicate head `END` symbols.
    end_def_symbols_lhs, end_def_symbols_rhs = (
        [symbol for symbol in graph_lt.heads if symbol.kind == SymbolKind.END],
        [symbol for symbol in graph_rt.heads if symbol.kind == SymbolKind.END],
    )

    assert (
        len(end_def_symbols_lhs) <= 1 and len(end_def_symbols_rhs) <= 1
    ), f"Duplicate `END` initial symbols {end_def_symbols_lhs} and {end_def_symbols_rhs}."

    if end_def_symbols_lhs and end_def_symbols_rhs:
        graph_rt.heads.remove(end_def_symbols_rhs[0])

    # Remove duplicate tail `END` symbols.
    end_def_symbols_lhs, end_def_symbols_rhs = (
        [symbol for symbol in graph_lt.tails if symbol.kind == SymbolKind.END],
        [symbol for symbol in graph_rt.tails if symbol.kind == SymbolKind.END],
    )

    assert (
        len(end_def_symbols_lhs) <= 1 and len(end_def_symbols_rhs) <= 1
    ), "Duplicate `END` final symbols."

    if end_def_symbols_lhs and end_def_symbols_rhs:
        predecessors = [
            parent
            for parent, children in graph_rt.edges.items()
            if end_def_symbols_rhs[0] in children
        ]

        for predecessor in predecessors:
            edges[predecessor].remove(end_def_symbols_rhs[0])
            edges[predecessor].add(end_def_symbols_lhs[0])

        graph_rt.tails.remove(end_def_symbols_rhs[0])

    return SymbolGraph(
        heads=graph_lt.heads | graph_rt.heads,
        edges=edges,
        tails=graph_lt.tails | graph_rt.tails,
    )


class DelimiterProperty(IntFlag):
    NULL = 0 << 0
    STOP = 1 << 0
    LOOP = 1 << 1
    PIPE = 1 << 2


def cast_symbol_graph(graph: SymbolGraph, kind: DelimiterProperty):
    initials, edges, finals = (graph.heads, graph.edges, graph.tails)

    end_def_symbol = (
        next((s for s in initials if s.kind == SymbolKind.END), None)
        or next((s for s in finals if s.kind == SymbolKind.END), None)
        or Symbol("", SymbolKind.END)
    )

    if kind & DelimiterProperty.LOOP:
        # Need to re-establish the loop for mixed graphs built through unions.
        if end_def_symbol in finals:
            finals.update(
                {
                    parent
                    for parent, children in edges.items()
                    if end_def_symbol in children
                }
            )

        for final in finals:
            for initial in initials:
                # Nested casts would lead to duplicates.
                if final.kind != SymbolKind.END:
                    edges[final].add(initial)

            if final.kind != SymbolKind.END:
                edges[final].add(end_def_symbol)

        graph.tails = {end_def_symbol}

    elif kind & DelimiterProperty.STOP:
        if end_def_symbol not in initials:
            graph.heads.add(end_def_symbol)

        edges[end_def_symbol] = set()

    return graph


@dataclass(slots=True)
class TrailBuilder:
    graph: SymbolGraph
    kind: DelimiterProperty
    tag: Optional[str]

    @classmethod
    def new(cls):
        return TrailBuilder(
            graph=SymbolGraph.new(), kind=DelimiterProperty.NULL, tag=None
        )


def build_symbol_graph(definition: str):
    LEXEME_TO_KIND = {
        "(": DelimiterProperty.NULL,
        "{": DelimiterProperty.LOOP,
        "[": DelimiterProperty.STOP,
        "|": DelimiterProperty.PIPE,
    }

    lexemes = split_definition_into_lexemes(definition)
    state: list[TrailBuilder] = [TrailBuilder.new()]
    accumulated: list[str] = []
    i = 0

    while i < len(lexemes):
        lexeme = lexemes[i]

        if lexeme in "([{|":
            accumulated_graph = construct_symbol_graph(accumulated)
            state[-1].graph = connect_symbol_graph(state[-1].graph, accumulated_graph)
            accumulated.clear()

            state.append(TrailBuilder(SymbolGraph.new(), LEXEME_TO_KIND[lexeme], None))

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

            if tag := accumulator.tag:
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
