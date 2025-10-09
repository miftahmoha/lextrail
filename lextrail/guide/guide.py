from collections import defaultdict, deque
from copy import copy
from dataclasses import dataclass, field
from itertools import chain
from os import getenv
from typing import Deque, Generator

from lextrail.assemble import ASMGraph, build_asm_graph
from lextrail.base import Symbol, SymbolGraph, SymbolType
from lextrail.build import build_symbol_graph
from lextrail.exceptions import ParsingError
from lextrail.guide.passes import (
    check_for_potential_infinite_loops,
    divide_cfg_into_rules,
)
from lextrail.helpers import is_end_def_symbol


def build_cfg_graphs(cfg_grammar: str) -> dict[str, SymbolGraph]:
    cfg_rules = divide_cfg_into_rules(cfg_grammar)
    cfg_graphs = {
        symbol: build_symbol_graph(graph) for symbol, graph in cfg_rules.items()
    }

    # [TODO] Make it optional?
    for symbol_name, symbol_def in cfg_rules.items():
        # [NOTE] Check for potential infinite loops in the CFG.
        # (1) WARNING: There is an infinite loop but there exists a path to escape to it.
        # (2) EXCEPTION: There is an infinite loop but there is no escape.
        check_for_potential_infinite_loops(
            symbol_name, symbol_def, cfg_graphs[symbol_name]
        )

    return cfg_graphs


@dataclass(slots=True)
class TrailGraph:
    graph: SymbolGraph
    label: str
    state: Symbol = Symbol()

    def serialize(self):
        return {
            "graph": self.graph.serialize(),
            "state": self.state.serialize() if self.state else "",
            "label": self.label,
        }


@dataclass(slots=True)
class TrailProposal:
    state: Deque[TrailGraph]
    symbol: Symbol = Symbol()

    def __bool__(self):
        return bool(self.symbol) and bool(self.state)


@dataclass(slots=True)
class Trail:
    graphs: dict[str, SymbolGraph]
    backrefs: dict[str, dict[int, str]] = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(str))
    )
    assembler: ASMGraph = field(default_factory=lambda: ASMGraph())


def trail_expr(expression: str, vocabulary: list[str] = []):
    return Trail(
        graphs=build_cfg_graphs(f"start: {expression}"),
        assembler=build_asm_graph(vocabulary),
    )


def trail_regex(regex: str, vocabulary: list[str] = []):
    return Trail(
        graphs=build_cfg_graphs(f"start: /{regex}/"),
        assembler=build_asm_graph(vocabulary),
    )


def trail_cfg(grammar: str, vocabulary: list[str] = []):
    return Trail(
        graphs=build_cfg_graphs(grammar), assembler=build_asm_graph(vocabulary)
    )


def get_next_proposal(
    trail: Trail, proposal: TrailProposal
) -> Generator[TrailProposal, None, None]:
    curr_state, curr_symbol = proposal.state, proposal.symbol
    curr_graph = curr_state[-1].graph

    if int(getenv("PARSE_BREFS", 0)) and (curr_symbol.s_type == SymbolType.TERMINAL):
        capture_backrefs(trail, proposal)

    next_symbols = curr_graph.tree[curr_symbol] if curr_symbol else curr_graph.initials

    if not next_symbols:
        curr_state.pop()

        # Reaches the end of the path.
        if not curr_state:
            return

        # Last symbol where we left.
        curr_symbol = curr_state[-1].state

        yield from get_next_proposal(
            trail, TrailProposal(symbol=curr_symbol, state=curr_state)
        )

    for next_symbol in next_symbols:
        if next_symbol.s_type in [
            SymbolType.TERMINAL,
            SymbolType.REGEX,
        ] or is_end_def_symbol(next_symbol):
            # A shallow copy is needed for each proposal, in order to avoid overwriting a state
            # through other execution paths.
            next_state = deque([copy(state) for state in curr_state])
            next_state[-1].state = next_symbol

            yield TrailProposal(symbol=next_symbol, state=next_state)

        if next_symbol.s_type == SymbolType.NON_TERMINAL:
            # A shallow copy is needed for each proposal, in order to avoid overwriting a state
            # through other execution paths.
            next_state = deque([copy(state) for state in curr_state])
            next_state[-1].state = next_symbol

            # Reaching a `NON_TERMINAL` means adding a layer to the stack.
            next_layer = TrailGraph(
                graph=trail.graphs[next_symbol.content],
                label=next_symbol.content,
            )
            next_state.append(next_layer)

            yield from get_next_proposal(trail, TrailProposal(state=next_state))

        if next_symbol.s_type == SymbolType.REFERENCE:
            # A reference must be a unique proposal.
            if len(next_symbols) > 1:
                raise ParsingError("Reference symbol is not unique.")

            index = int(next_symbol.content[1:])
            reference = trail.backrefs[curr_state[-1].label]

            if (index + 1) not in reference.keys():
                raise ParsingError(
                    f"Invalid backreference `\\{index}`: Missing or contains non-terminal symbols."
                )

            next_symbol.s_type, next_symbol.content = (
                SymbolType.TERMINAL,
                f'"{reference[index + 1]}"',
            )

            yield TrailProposal(symbol=next_symbol, state=proposal.state)


def get_next_proposals(
    trail: Trail, proposals: list[TrailProposal] = []
) -> list[TrailProposal]:
    if not proposals:
        start = TrailGraph(graph=trail.graphs["start"], label="start")
        return list(get_next_proposal(trail, TrailProposal(state=deque([start]))))

    assert (
        proposal.symbol.content == proposals[0].symbol.content for proposal in proposals
    ), "Ambiguous symbols must have identical content."
    return list(
        chain.from_iterable(
            get_next_proposal(trail, proposal) for proposal in proposals
        )
    )


# [TODO] Add tests for `reference_indices`.
# Each symbol has two indentifiers, which are `count` and `depth`.
# The count is the literal index of the subgraph which is the backreference index.
# Example: ( {COUNT, DEPTH = 1} `def_1` ( {COUNT, DEPTH = 2} `def_2` ) {COUNT, DEPTH = 1} `def_3` ).
# If the chosen symbol is at a certain `count = Z`, then (1) we add its content to the
# backreference at the depth `self._built_symbol_graph.metadata["_COUNT_TO_DEPTH"][Z]`,
# and (2) if its `depth = Y` is > 1, we add its content to the backreferences which have less depth.
# Thus, we must find the counts at which the depth is < Y.
# Another detail is the maximum, since adjacent graphs have the same depth,
# there'll be many counts with depth `X-1`, but the content should be added to the closest index.
def resolve_counts(count, _COUNT_TO_DEPTH: dict[int, int]) -> list[int]:
    result = [count]
    curr_count = count
    curr_depth = _COUNT_TO_DEPTH[count] - 1

    while curr_depth >= 1:
        next_count = max(
            (
                k
                for k in _COUNT_TO_DEPTH.keys()
                if k < curr_count and _COUNT_TO_DEPTH[k] == curr_depth
            ),
            default=None,
        )

        if next_count is None:
            break

        result.append(next_count)
        curr_count = next_count
        curr_depth -= 1

    return result


def capture_backrefs(trail: Trail, proposal: TrailProposal):
    curr_symbol, curr_state = proposal.symbol, proposal.state

    if is_end_def_symbol(curr_symbol):
        return

    label = curr_state[-1].label

    counts = resolve_counts(
        curr_symbol.s_metadata["_COUNT"],
        trail.graphs[label].metadata["_COUNT_TO_DEPTH"],
    )

    for count in counts:
        trail.backrefs[label][count] += curr_symbol.content

    # Propagating references into upper layers.
    for layer in list(curr_state)[:-1]:
        state_symbol, state_label = layer.state, layer.label

        assert layer.state is not None, "None state was found while backreferencing."

        counts = resolve_counts(
            state_symbol.s_metadata["_COUNT"],
            trail.graphs[state_label].metadata["_COUNT_TO_DEPTH"],
        )

        for count in counts:
            trail.backrefs[state_label][count] += curr_symbol.content
            # Pop backereferences that contain non-terminal symbols.
            # [TODO] There is an issue with the approach.
            # trail.references[state_label].pop(index, None)
