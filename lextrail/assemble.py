from typing import Optional
from collections import defaultdict
import uuid

from lextrail.base import CFGGenerationState, CFGStatefulGraph, Symbol, SymbolType
from lextrail.build.passes import _build_symbol_from_string
from lextrail.exceptions import CombineError

# Aliasing.
char = str


class AssemblyNode:
    def __init__(self, content: str):
        self.content = content
        self.id = uuid.uuid4()

    def __hash__(self):
        return hash((self.content, self.id))

    def __eq__(self, other):
        # Ensure equality is checked for all fields.
        if not isinstance(other, AssemblyNode):
            return False

        return (self.content == other.content) and (self.id == other.id)


class AssemblyGraph:
    def __init__(
        self,
        *,
        initials: list[AssemblyNode],
        tree: dict[AssemblyNode, list[AssemblyNode]],
        finals: list[AssemblyNode],
        states: dict[AssemblyNode, str] = {},
    ):
        self.initials = initials
        self.tree = tree
        self.finals = finals
        self.states = states

    def __eq__(self, other) -> bool:
        if isinstance(other, AssemblyGraph):
            return (self.initials == other.initials) and (self.tree == other.tree)
        return NotImplemented

    def __bool__(self) -> bool:
        return bool(self.initials) and bool(self.tree) and bool(self.finals)

    def copy(self):
        return AssemblyGraph(
            initials=self.initials,
            tree=self.tree,
            finals=self.finals,
            states=self.states.copy(),
        )


def _fetch_assemble_node_from_content(
    assembly_nodes: list[AssemblyNode], character: char
) -> Optional[AssemblyNode]:
    return next((node for node in assembly_nodes if node.content == character), None)


def _assemble_graph(vocabulary: list[str]) -> AssemblyGraph:
    initials: list[AssemblyNode] = []
    tree: dict[AssemblyNode, list[AssemblyNode]] = defaultdict(list)
    finals: list[AssemblyNode] = []

    is_common_subgraph: bool = False
    for word in vocabulary:
        i = 0
        wordlist = list(word)

        while i < len(wordlist):
            character = wordlist[i]

            if i == 0:
                if token_node := _fetch_assemble_node_from_content(initials, character):
                    previous = token_node
                    is_common_subgraph = True
                else:
                    previous = AssemblyNode(character)
                    initials.append(previous)
                i += 1
                continue

            if is_common_subgraph:
                if token_node := _fetch_assemble_node_from_content(tree[previous], character):  # type: ignore
                    previous = token_node
                else:
                    next = AssemblyNode(character)
                    tree[previous].append(next)  # type: ignore
                    previous = next
                    is_common_subgraph = False
                i += 1
                continue

            next = AssemblyNode(character)
            tree[previous].append(next)  # type: ignore
            previous = next
            i += 1

        finals.append(previous)  # type: ignore

    return AssemblyGraph(initials=initials, tree=tree, finals=finals)


def _get_next_assemble_graph(
    graph: AssemblyGraph, next_terminal: char, _IS_START: bool = False
) -> tuple[AssemblyGraph, list[str]]:

    assembled: list[str] = []

    if _IS_START and (
        assemble_node := _fetch_assemble_node_from_content(
            graph.initials, next_terminal[1:-1]
        )
    ):
        graph.states[assemble_node] = next_terminal[1:-1]
    else:
        completed = []
        for node in graph.states.copy().keys():
            for next_node in graph.tree[node]:
                if next_node.content == next_terminal[1:-1]:
                    graph.states[next_node] = graph.states.pop(node) + next_node.content
                    if next_node in graph.finals:
                        completed.append(graph.states[next_node])
                    break
            graph.states.pop(node, None)

        assembled.extend(completed)

    return graph, assembled


def _extract_single_token_proposal(
    next_terminals_w_states: dict[Symbol, CFGGenerationState],
    symbol_next: Symbol,
    assembled: str,
) -> dict[Symbol, CFGGenerationState]:
    valid_paths: dict[Symbol, CFGGenerationState] = {}

    if symbol_next.s_type == SymbolType.TERMINAL:
        combination_symbol = _build_symbol_from_string(
            '"' + assembled + '"'
        )  # Adding the `<">..<">` for terminals.
        # Avoids writing to the reference.
        combination_state = next_terminals_w_states[symbol_next].copy()
        # Give `symbol_next`'s connections to `combination_symbol`.
        # [NOTE] Always going to be so, if a symbol exists in `next_terminals_w_states.keys()`
        # then it'll have a history.
        # [NOTE] In case the LLM picks the concatenated symbol,
        # we search for its corresponding symbol, then search for the next connections.
        if combination_state:
            # [NOTE] Modifying a reference, it doesn't really matter that we're referencing `.tree`
            # (copy depth stops at `.graph`), we don't change `combination_state[-1].graph.tree[symbol_next]`
            # during the process.
            combination_state[-1].graph.tree[combination_symbol] = combination_state[
                -1
            ].graph.tree[symbol_next]
        # Add path.
        valid_paths[combination_symbol] = combination_state
    else:
        raise CombineError(
            "Expected `SymbolType.TERMINAL` got `{symbol_prev.s_type}` instead."
        )

    return valid_paths


def _update_single_token_combinations(
    guide,
    graph: AssemblyGraph,
):
    proposals: dict[Symbol, CFGStatefulGraph | CFGGenerationState] = {}

    def recurse_update(
        next_terminals_w_states: dict[Symbol, CFGGenerationState],
        next_graph: AssemblyGraph,
        _IS_START: bool = False,
    ):
        nonlocal proposals

        for symbol_next, state_next in next_terminals_w_states.items():
            current_graph, completed = _get_next_assemble_graph(
                next_graph.copy(), symbol_next.content, _IS_START=_IS_START
            )

            for completion in completed:
                proposal = _extract_single_token_proposal(
                    next_terminals_w_states, symbol_next, completion
                )
                proposals.update(proposal)

            if not current_graph.states:
                continue

            guide._get_next_terminals([symbol_next], [state_next])
            recurse_update(guide._next_terminals_w_states.copy(), current_graph)

    # Get `next_terminals_w_states`.
    next_terminals_w_states = guide._next_terminals_w_states.copy()
    # Run.
    recurse_update(next_terminals_w_states, graph, _IS_START=True)
    # Update `cfg_generation_state`.
    next_terminals_w_states.update(proposals)

    return next_terminals_w_states
