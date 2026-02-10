from collections import defaultdict
from dataclasses import dataclass
from typing import Deque, Optional
from copy import copy
from collections import deque

import sys
import warnings

from lextrail.helpers import TrailError, format_error
from lextrail.build import (
    Symbol,
    SymbolGraph,
    SymbolKind,
    split_definition_into_lexemes,
    build_symbol_graph,
)
from lextrail.helpers import (
    consume_lexeme,
    is_escaped,
    contains_special_characters,
    bfs,
    format_error,
)


def split_cfg_into_lines(grammar: str) -> list[str]:
    rules: list[str] = []
    in_quote = False
    in_slash = False
    rule: list[str] = []
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
            consume_lexeme(rules, rule)
            i += 1
            continue

        rule.append(curr)
        i += 1

    consume_lexeme(rules, rule)

    return rules


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

    lines = split_cfg_into_lines(grammar)

    for line in lines:

        if line.isspace():
            continue

        head, body = split_production(line)

        if not head and not body:
            if not current:
                raise TrailError(format_error("Invalid production.", "", line))

            cfg[current] += line
        else:
            if contains_special_characters(head):
                raise TrailError(
                    format_error(
                        f"Name `{head}` contains special characters.", "", line.strip()
                    )
                )

            if head in cfg.keys():
                raise TrailError(
                    format_error(f"Duplicate production.", "", line.strip())
                )

            cfg[head] = body
            current = head

    if "start" not in cfg.keys():
        raise TrailError("`start` production rule has not been defined.")

    return cfg


def is_escapable_from_infinite_loop(graph: "SymbolGraph", prospect: str) -> bool:
    visited = []
    queue: Deque[Symbol] = deque(graph.head)

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
            queue.extend(graph.tree[vertex])

    return False


def contains_infinite_loop(graph: "SymbolGraph", head: str, body: str) -> bool:
    is_loop = head in split_definition_into_lexemes(body)

    if is_loop:
        warnings.warn(
            f"A potential loop of non-terminal symbols exists in {head}: {body}."
        )

        if not is_escapable_from_infinite_loop(graph, head):
            return True

    return False


def contains_excluded_vars(graph: "SymbolGraph", heads: list[str]) -> bool:
    excluded = next(
        (
            symbol.content
            for symbol in graph.symbols
            if symbol.content not in heads and symbol.kind == SymbolKind.VARIABLE
        ),
        None,
    )

    if excluded:
        print(f"{excluded} was not defined in the CFG.", file=sys.stderr)
        return True
    else:
        return False


@dataclass
class TrailLayer:
    graph: "SymbolGraph"
    node: Optional["Symbol"]


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
                format_error("Production has an infinite loop.", head, body)
            )

        if contains_excluded_vars(graph, productions.keys()):
            raise TrailError(
                format_error("Production has an undefined variable.", head, body)
            )

        graphs[head] = graph

    return graphs


def trail_cfg(cfg: str):
    return Trail(schema=build_cfg_graph(cfg), state=TrailState.new())


def trail_exp(exp: str):
    return Trail(schema=build_cfg_graph(f"start: {exp}"), state=TrailState.new())


def trail_rex(exp: str):
    return Trail(schema=build_cfg_graph(f"start: /{exp}/"), state=TrailState.new())


def trail_run(trail: Trail):
    schema, state = trail.schema, trail.state
    proposals, backrefs = state.proposals, state.backrefs

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

        # === Backreferences ===
        if node is not None and node.kind == SymbolKind.TERMINAL:
            for tag in node.tags:
                backrefs[tag] += node.content

        successors = graph.tree[node] if node else graph.head

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

                # Reaching a `VARIABLE` means adding a layer to the stack.
                next_layer = TrailLayer(graph=schema[next_value], node=None)
                next_frame.append(next_layer)

                # Push it to be processed.
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
