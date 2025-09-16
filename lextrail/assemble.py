import uuid
from collections import defaultdict
from typing import Dict, List, Optional, cast

from lextrail.base import CFGGenerationState, CFGStatefulGraph, Symbol, SymbolType
from lextrail.build.passes import build_symbol_from_content
from lextrail.exceptions import CombineError

# [TODO] Create a character type with runtime validation.
char = str


class AssemblyNode:
    def __init__(self, content: str = ""):
        self.content = content
        self.id = uuid.uuid4()

    def __hash__(self):
        return hash((self.content, self.id))

    def __eq__(self, other):
        # Ensure equality is checked for all fields.
        if not isinstance(other, AssemblyNode):
            return False

        return (self.content == other.content) and (self.id == other.id)

    def __bool__(self):
        return bool(self.content)


AssemblyTree = Dict[AssemblyNode, List[AssemblyNode]]


class AssemblyState:
    def __init__(self, node: Optional[AssemblyNode] = None, accu: str = ""):
        self.node = node
        self.accu = accu

    def __bool__(self):
        return bool(self.node) and bool(self.accu)


class AssemblyGraph:
    def __init__(
        self,
        initials: List[AssemblyNode] = [],
        tree: AssemblyTree = {},
        finals: List[AssemblyNode] = [],
    ):
        self.initials = initials
        self.tree = tree
        self.finals = finals

    def __eq__(self, other) -> bool:
        if isinstance(other, AssemblyGraph):
            return (self.initials == other.initials) and (self.tree == other.tree)
        return NotImplemented

    def __bool__(self) -> bool:
        return bool(self.initials) and bool(self.tree) and bool(self.finals)


def build_assembly_graph(vocabulary: list[str]) -> AssemblyGraph:
    initials: List[AssemblyNode] = []
    tree: AssemblyTree = defaultdict(list)
    finals: List[AssemblyNode] = []

    for word in vocabulary:
        current_node = AssemblyNode()

        for i, char in enumerate(word):
            candidates = initials if i == 0 else tree[current_node]

            existing_node = next(
                (node for node in candidates if node.content == char), None
            )
            if existing_node:
                current_node = existing_node
            else:
                new_node = AssemblyNode(char)
                candidates.append(new_node)
                current_node = new_node

        # Guards against empty words.
        if current_node:
            finals.append(current_node)

    return AssemblyGraph(initials=initials, tree=tree, finals=finals)


def build_assembly_proposal(
    last_symbol: Symbol,  # [NOTE] They're called `last` for a reason, they're last in the assembly sequence.
    last_state: CFGGenerationState,
    assembled_content: str,
) -> dict[Symbol, CFGGenerationState]:
    if last_symbol.s_type != SymbolType.TERMINAL:
        raise CombineError(
            "Expected `SymbolType.TERMINAL` got `{symbol_prev.s_type}` instead."
        )

    assembled_symbol = build_symbol_from_content(f'"{assembled_content}"')

    # [NOTE] We add a connection to the assembled state, a shallow copy is needed.
    assembled_state = last_state.copy()

    if assembled_state:
        # (*) Copy tree connections from the last assembled symbol to combined symbol.
        last_graph = assembled_state[-1].graph
        last_graph.tree[assembled_symbol] = last_graph.tree[assembled_symbol]

    return {assembled_symbol: assembled_state}


def update_single_token_combinations(
    guide,
    assembly_graph: AssemblyGraph,
):
    proposals: dict[Symbol, CFGStatefulGraph | CFGGenerationState] = {}

    def recurse_update(
        next_terminals_w_states: dict[Symbol, CFGGenerationState],
        state: AssemblyState = AssemblyState(),
    ):
        nonlocal proposals

        for symbol_next, state_next in next_terminals_w_states.items():
            # [TODO][PARALLELISM] Each trajectory could be a core.
            # Each trajectory should have its own state instance, interference shouldn't happen.
            current_state = AssemblyState(state.node, state.accu)

            if not current_state:
                assemble_node = next(
                    (
                        candidate
                        for candidate in assembly_graph.initials
                        if candidate.content == symbol_next.content[1:-1]
                    ),
                    None,
                )

                if assemble_node is None:
                    continue
                else:
                    current_state.node = assemble_node
                    current_state.accu = symbol_next.content[1:-1]
            else:
                # `mypy` does not reason about the custom implementation of `__bool__` for `AssemblyState`.
                candidates = assembly_graph.tree.get(
                    cast(AssemblyNode, current_state.node), []
                )

                assemble_node = next(
                    (
                        candidate
                        for candidate in candidates
                        if candidate.content == symbol_next.content[1:-1]
                    ),
                    AssemblyNode(),
                )
                if assemble_node.content == symbol_next.content[1:-1]:
                    current_state.node = assemble_node
                    current_state.accu += symbol_next.content[1:-1]
                else:
                    continue

                if assemble_node in assembly_graph.finals:
                    proposal = build_assembly_proposal(
                        symbol_next, state_next, current_state.accu
                    )
                    proposals.update(proposal)

            # [TODO] Turn `get_next_terminals` into one single function.
            guide.get_next_terminals_temp(symbol_next, state_next)
            recurse_update(guide._next_terminals_w_states.copy(), current_state)

    # [TODO] Avoid the multiple copies through a more functional approach.
    next_terminals_w_states = guide._next_terminals_w_states.copy()
    recurse_update(next_terminals_w_states)
    next_terminals_w_states.update(proposals)

    return next_terminals_w_states
