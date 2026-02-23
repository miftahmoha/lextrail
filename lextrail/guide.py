import warnings
from collections import defaultdict, deque
from collections.abc import KeysView
from copy import copy
from dataclasses import dataclass
from typing import Deque, Optional

from lextrail.build import (
    Symbol,
    SymbolGraph,
    SymbolKind,
    build_symbol_graph,
    split_definition_into_lexemes,
)
from lextrail.helpers import (
    TrailError,
    bfs,
    consume_lexeme,
    contains_special_characters,
    format_error,
    is_escaped,
)


def split_cfg_into_rows(grammar: str) -> list[str]:
    rows: list[str] = []
    in_quote = False
    in_slash = False
    row: list[str] = []
    i = 0

    while i < len(grammar):
        curr = grammar[i]

        if curr == '"':
            if not in_quote and not in_slash:
                in_quote = True
            elif in_quote and not is_escaped(grammar, i):
                in_quote = False
        elif curr == "/":
            if not in_quote and not in_slash:
                in_slash = True
            elif in_slash and not is_escaped(grammar, i):
                in_slash = False
        elif curr == "\n" and not in_quote and not in_slash:
            consume_lexeme(rows, row)
            i += 1
            continue

        row.append(curr)
        i += 1

    consume_lexeme(rows, row)

    return rows


def split_production(production: str) -> tuple[str, str]:
    indices: list[int] = []
    in_quote = False
    in_slash = False
    i = 0

    while i < len(production):
        curr = production[i]

        if curr == '"':
            if not in_quote and not in_slash:
                in_quote = True
            elif in_quote and not is_escaped(production, i):
                in_quote = False
        elif curr == "/":
            if not in_quote and not in_slash:
                in_slash = True
            elif in_slash and not is_escaped(production, i):
                in_slash = False
        elif curr == ":":
            if not in_quote and not in_slash:
                indices.append(i)

        i += 1

    match len(indices):
        case 0:
            return ("", "")
        case 1:
            return (
                production[: indices[0]].strip(),
                production[indices[0] + 1 :].strip(),
            )

        case _:
            raise TrailError(
                format_error(
                    "Duplicate separator `:`.",
                    production[: indices[0]].strip(),
                    production[indices[0] : indices[1] + 1].strip(),
                )
            )


def divide_cfg_into_productions(grammar: str) -> dict[str, str]:
    cfg: dict[str, str] = {}
    current = ""

    rows = split_cfg_into_rows(grammar)

    for row in rows:

        if row.isspace():
            continue

        heads, body = split_production(row)

        if not heads and not body:
            if not current:
                raise TrailError(format_error("Invalid production.", "", row))

            cfg[current] += row
        else:
            if contains_special_characters(heads):
                raise TrailError(
                    format_error(
                        f"Name `{heads}` contains special characters.", "", row.strip()
                    )
                )

            if heads in cfg.keys():
                raise TrailError(format_error("Duplicate production.", "", row.strip()))

            cfg[heads] = body
            current = heads

    if "start" not in cfg.keys():
        raise TrailError(
            format_error("`start` production rule has not been defined.", "", "")
        )

    return cfg


def is_escapable_from_infinite_loop(graph: "SymbolGraph", prospect: str) -> bool:
    visited = []
    queue: Deque[Symbol] = deque(graph.heads)

    while queue:
        vertex = queue.popleft()

        # If the vertex is a `infinite` symbol, then it means the (infinite) path is closed.
        if vertex.content == prospect and vertex.kind == SymbolKind.VARIABLE:
            continue

        # If not, we'll do a DFS/BFS traversal starting at the vertex, it means either
        # (1) there aren't any infinite nodes, thus the path is open and an escape exists,
        # or (2) there are some `infinite` nodes and we can't make a conclusion. In such case,
        # we go to the next nodes and repeat.
        visited_at_vertex = [
            symbol
            for symbol in bfs(graph, [vertex])
            if symbol.kind == SymbolKind.VARIABLE
        ]

        if all(symbol.content != prospect for symbol in visited_at_vertex):
            return True

        if vertex not in visited:
            visited.append(vertex)
            queue.extend(graph.edges[vertex])

    return False


def contains_infinite_loop(graph: "SymbolGraph", heads: str, body: str) -> bool:
    is_loop = heads in split_definition_into_lexemes(body)

    if is_loop:
        warnings.warn(
            f"A potential loop of non-terminal symbols exists in {heads}: {body}."
        )

        if not is_escapable_from_infinite_loop(graph, heads):
            return True

    return False


def contains_undefined_vars(
    graph: "SymbolGraph", heads: KeysView[str]
) -> Optional[str]:
    return next(
        (
            symbol.content
            for symbol in graph.symbols
            if symbol.content not in heads and symbol.kind == SymbolKind.VARIABLE
        ),
        None,
    )


@dataclass
class TrailLayer:
    graph: "SymbolGraph"
    node: Optional["Symbol"]

    def serialize(self):
        return {
            "graph": self.graph.serialize(),
            "state": self.node.serialize() if self.node else "",
        }


@dataclass
class TrailFrame:
    @classmethod
    def new(cls, schema: "CFGGraph") -> list["TrailLayer"]:
        return [TrailLayer(graph=schema["start"], node=None)]


@dataclass
class TrailProposal:
    frame: list[TrailLayer]
    value: str


type TrailRefs = dict[str, str]


@dataclass
class TrailState:
    proposals: list[TrailProposal]
    backrefs: TrailRefs

    @classmethod
    def new(cls) -> "TrailState":
        return TrailState(proposals=[], backrefs=defaultdict(str))


type CFGGraph = dict[str, SymbolGraph]


@dataclass
class Trail:
    schema: CFGGraph
    state: TrailState


def build_cfg_graph(grammar: str) -> CFGGraph:
    graphs: CFGGraph = {}

    productions = divide_cfg_into_productions(grammar)

    for head, body in productions.items():
        graph = build_symbol_graph(body)

        if contains_infinite_loop(graph, head, body):
            raise TrailError(
                format_error(
                    "Production has an infinite loop.",
                    f"{head}: ",
                    body,
                )
            )

        if undefined := contains_undefined_vars(graph, productions.keys()):
            raise TrailError(
                format_error(
                    f"Production has an undefined variable `{undefined}`.",
                    f"{head}: ",
                    body,
                )
            )

        graphs[head] = graph

    return graphs


def trail_cfg(cfg: str):
    return Trail(schema=build_cfg_graph(cfg), state=TrailState.new())


def trail_exp(exp: str):
    return Trail(schema=build_cfg_graph(f"start: {exp}"), state=TrailState.new())


def trail_rex(exp: str):
    return Trail(schema=build_cfg_graph(f"start: /{exp}/"), state=TrailState.new())


def trail_run(core: Trail):
    schema, state = core.schema, core.state
    proposals, backrefs = state.proposals, state.backrefs

    for proposal in proposals:
        node, value = proposal.frame[-1].node, proposal.value

        if node and (tags := node.tags):
            for tag in tags:
                backrefs[tag] += value

    frames = (
        [proposal.frame for proposal in proposals]
        if proposals
        else [TrailFrame.new(schema)]
    )

    state.proposals.clear()

    while frames:
        frame = frames.pop()
        checkpoint = frame[-1]
        graph, node = (checkpoint.graph, checkpoint.node)

        successors = graph.edges[node] if node else graph.heads

        if not successors:
            frame.pop()

            if frame:
                frames.append(frame)

            continue

        for successor in successors:
            if successor.kind == SymbolKind.TERMINAL:
                next_frame = [copy(layer) for layer in frame]
                next_frame[-1].node = successor
                next_value = successor.content

                state.proposals.append(
                    TrailProposal(frame=next_frame, value=next_value)
                )
            elif successor.kind == SymbolKind.VARIABLE:
                next_frame = [copy(layer) for layer in frame]
                next_frame[-1].node = successor
                next_value = successor.content

                next_layer = TrailLayer(graph=schema[next_value], node=None)
                next_frame.append(next_layer)

                frames.append(next_frame)
            elif successor.kind == SymbolKind.REFERENCE:
                next_frame = [copy(layer) for layer in frame]
                next_frame[-1].node = successor
                next_value = backrefs[successor.content]

                state.proposals.append(
                    TrailProposal(frame=next_frame, value=next_value)
                )
            elif successor.kind == SymbolKind.END:
                next_frame = [copy(layer) for layer in frame]
                next_frame[-1].node = successor

                state.proposals.append(TrailProposal(frame=next_frame, value=""))
            else:
                raise TrailError("Symbol of kind `{successor.kind}` is not supported.")


def get_next_values(trail: Trail, value: str):
    state = trail.state

    current = state.proposals
    state.proposals = [proposal for proposal in current if proposal.value == value]

    if current and not state.proposals:
        raise TrailError(f"`{value}` has no previous state.")

    trail_run(trail)

    return [proposal.value for proposal in state.proposals]
