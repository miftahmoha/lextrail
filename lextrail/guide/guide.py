from collections import defaultdict, deque
from copy import copy
from dataclasses import dataclass, field
from itertools import chain
from typing import Deque, Generator

from lextrail.assemble import ASMGraph, build_asm_graph
from lextrail.base import Symbol, Symbol_Kind, SymbolGraph
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
    graph: SymbolGraph  # [TODO] Why not initialized?
    label: str  # [TODO] Why not initialized?
    state: Symbol = Symbol()

    def serialize(self):
        return {
            "graph": self.graph.serialize(),
            "state": self.state.serialize() if self.state else "",
            "label": self.label,
        }


@dataclass(slots=True)
class TrailProposal:
    state: Deque[TrailGraph]  # [TODO] Why not initialized?
    symbol: Symbol = Symbol()  # [TODO] Why not initialized?

    def __bool__(self):
        return bool(self.symbol) and bool(self.state)


@dataclass(slots=True)
class Trail:
    graphs: dict[str, SymbolGraph]  # [TODO] Why not initialized?
    backrefs: dict[str, str] = field(default_factory=lambda: defaultdict(str))
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

    if (tags := curr_symbol.tags) and curr_symbol.kind == Symbol_Kind.TERMINAL:
        for tag in tags:
            trail.backrefs[tag] += curr_symbol.content

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
        if next_symbol.kind in [
            Symbol_Kind.TERMINAL,
            Symbol_Kind.REGEX,
        ] or is_end_def_symbol(next_symbol):
            # A shallow copy is needed for each proposal, in order to avoid overwriting a state
            # through other execution paths.
            next_state = deque([copy(state) for state in curr_state])
            next_state[-1].state = next_symbol

            yield TrailProposal(symbol=next_symbol, state=next_state)

        if next_symbol.kind == Symbol_Kind.VARIABLE:
            # A shallow copy is needed for each proposal, in order to avoid overwriting a state
            # through other execution paths.
            next_state = deque([copy(state) for state in curr_state])
            next_state[-1].state = next_symbol

            # Reaching a `VARIABLE` means adding a layer to the stack.
            next_layer = TrailGraph(
                graph=trail.graphs[next_symbol.content],
                label=next_symbol.content,
            )
            next_state.append(next_layer)

            yield from get_next_proposal(trail, TrailProposal(state=next_state))

        if next_symbol.kind == Symbol_Kind.REFERENCE:
            # A reference must be a unique proposal.
            if len(next_symbols) > 1:
                raise ParsingError("Reference symbol is not unique.")

            tag = next_symbol.content
            next_symbol.kind, next_symbol.content = (
                Symbol_Kind.TERMINAL,
                trail.backrefs[tag],
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
