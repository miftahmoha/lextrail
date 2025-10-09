import uuid
from collections import defaultdict, deque
from copy import copy
from itertools import chain
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Deque

from lextrail.base import Symbol
from lextrail.build import build_symbol_from_lexeme
from lextrail.exceptions import AssemblyError
from lextrail.helpers import TrailContext

if TYPE_CHECKING:
    from lextrail.guide import Trail, TrailGraph, TrailProposal

# Avoid circular import errors.
import lextrail.guide as Py_Module


@dataclass(slots=True)
class ASMNode:
    content: str = ""
    id: uuid.UUID = field(default_factory=lambda: uuid.uuid4())

    def __hash__(self):
        return hash(self.id)


@dataclass(slots=True)
class ASMState:
    node: ASMNode = ASMNode()
    acc: str = ""
    idx: int = 0


@dataclass(slots=True)
class ASMGraph:
    initials: list[ASMNode] = field(default_factory=list)
    tree: dict[ASMNode, list[ASMNode]] = field(
        default_factory=lambda: defaultdict(list)
    )
    finals: list[ASMNode] = field(default_factory=list)


def build_asm_graph(vocabulary: list[str]) -> ASMGraph:
    initials: list[ASMNode] = []
    tree: dict[ASMNode, list[ASMNode]] = defaultdict(list)
    finals: list[ASMNode] = []

    if not isinstance(vocabulary, list) and not all(
        isinstance(token, str) for token in vocabulary
    ):
        raise AssemblyError("The vocabulary must be list[str].")

    for word in vocabulary:
        current_node = ASMNode()

        for i, char in enumerate(word):
            candidates = initials if i == 0 else tree[current_node]

            existing_node = next(
                (node for node in candidates if node.content == char), None
            )
            if existing_node:
                current_node = existing_node
            else:
                new_node = ASMNode(char)
                candidates.append(new_node)
                current_node = new_node

        # Guards against empty words.
        if current_node:
            finals.append(current_node)

    return ASMGraph(initials=initials, tree=tree, finals=finals)


def build_asm_proposal(
    last_symbol: Symbol,
    last_state: Deque["TrailGraph"],  # [NOTE] They're last in the assembly sequence.
    asm_content: str,
) -> "TrailProposal":
    asm_symbol = build_symbol_from_lexeme(f'"{asm_content}"')

    # `last_state` gets update at `get_next_state`, which mutates `asm_state`.
    asm_state = deque([copy(state) for state in last_state])

    # `last_symbol` and `asm_symbol` get same state.
    asm_state[-1].state = asm_symbol
    asm_state[-1].graph.tree[asm_symbol] = last_state[-1].graph.tree[last_symbol]

    return Py_Module.TrailProposal(symbol=asm_symbol, state=asm_state)


def _next_asm_proposal(trail: "Trail", proposal: "TrailProposal", state: ASMState):
    curr_content, curr_state = proposal.symbol.content, proposal.state
    curr_idx, curr_acc = state.idx, state.acc
    curr_symbol = proposal.symbol

    candidates = trail.assembler.tree.get(state.node, [])

    if not candidates:
        return

    assemble_node = next(
        (
            candidate
            for candidate in candidates
            if candidate.content == curr_content[curr_idx]
        ),
        ASMNode(),
    )

    if assemble_node in trail.assembler.finals:
        next_proposal = build_asm_proposal(
            curr_symbol, curr_state, curr_acc + curr_content[curr_idx]
        )
        yield next_proposal

    next_idx = curr_idx + 1 if curr_content[curr_idx + 1 :] else 0
    next_proposals = (
        [proposal] if next_idx != 0 else Py_Module.get_next_proposals(trail, [proposal])
    )
    next_state = ASMState(assemble_node, curr_acc + curr_content[curr_idx], next_idx)

    for next_proposal in next_proposals:
        yield from _next_asm_proposal(trail, next_proposal, next_state)


def _get_asm_proposals(
    trail: "Trail",
    proposal: "TrailProposal",
):
    candidates = trail.assembler.initials
    curr_symbol, curr_state = proposal.symbol, proposal.state
    curr_content = curr_symbol.content

    if not candidates:
        return

    asm_node = next(
        (candidate for candidate in candidates if candidate.content == curr_content[0]),
        ASMNode(),
    )

    if asm_node in trail.assembler.finals:
        next_proposal = build_asm_proposal(curr_symbol, curr_state, curr_content[0])
        yield next_proposal

    next_idx = 0 if len(curr_content) == 1 else 1
    next_proposals = (
        [proposal] if next_idx == 1 else Py_Module.get_next_proposals(trail, [proposal])
    )
    next_state = ASMState(asm_node, curr_content, 0 if len(curr_content) == 1 else 1)

    for next_proposal in next_proposals:
        yield from _next_asm_proposal(trail, next_proposal, next_state)


def get_asm_proposals(
    trail: "Trail",
    proposals: list["TrailProposal"],
):
    with TrailContext(
        PARSE_BREFS="0"
    ):  # No reference captures during `get_next_proposals` calls.
        return list(
            chain.from_iterable(
                _get_asm_proposals(trail, proposal) for proposal in proposals
            )
        )
