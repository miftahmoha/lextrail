from typing import Optional
from dataclasses import dataclass, field
from copy import deepcopy
import uuid

from lextrail.base import Symbol, SymbolType, CFGGenerationState
from lextrail.build.passes import _build_symbol_from_string
from lextrail.guide import CFGGuide
from lextrail.exceptions import CombineError

# Aliasing.
char = str


@dataclass
class TokenNode:
    content: str
    s_id: uuid.UUID = field(default_factory=lambda: uuid.uuid4())

    def __hash__(self):
        return hash((self.content, self.s_id))

    def __eq__(self, other):
        # Ensure equality is checked for all fields.
        if not isinstance(other, TokenNode):
            return False

        return (self.content == other.content) and (self.s_id == other.s_id)


@dataclass
class TokenGraph:
    chain: dict[TokenNode, TokenNode]
    head: TokenNode
    state: Optional[TokenNode] = None

    def _build_string_from_tokens(self):
        if self.state is None:
            raise CombineError("Access to a string while state set to None.")
        out_as_string = ""
        out_as_token = self.head
        while out_as_token != self.state:
            out_as_string += out_as_token.content
            out_as_token = self.chain[out_as_token]
        return out_as_string

    def __eq__(self, other) -> bool:
        if isinstance(other, TokenGraph):
            return (self.head == other.head) and (self.chain == other.chain)
        return NotImplemented

    def __bool__(self) -> bool:
        return bool(self.head) and bool(self.chain)

    def copy(self):
        return deepcopy(self)


def _convert_tokens_into_graph(single_tokens: list[str]) -> list[TokenGraph]:
    graphs: list[TokenGraph] = []

    for single_token in single_tokens:
        chain: dict[TokenNode, TokenNode] = {}
        previous: Optional[TokenNode] = None

        for character in list(single_token):
            if previous:
                chain[previous] = TokenNode(character)
            else:
                previous = TokenNode(character)
                head = previous

        graphs.append(TokenGraph(chain=chain, head=head))  # type: ignore

    return graphs


def _fetch_next_graphs(
    next_terminal: char, graphs: list[TokenGraph], is_head: bool = False
):
    result: list[TokenGraph] = []

    if len(graphs) == 0:
        raise CombineError("Token graph array is empty.")

    if is_head:
        for graph in graphs:
            if (head := graph.head).content == next_terminal:
                graph.state = head
                result.append(graph)
    else:
        for graph in graphs:
            if graph.chain[graph.state].content == next_terminal:  # type: ignore
                graph.state = graph.chain[graph.state]  # type: ignore
                result.append(graph)

    return result


def _extract_finalized_graph(graphs: list[TokenGraph]) -> list[TokenGraph]:
    result: list[TokenGraph] = []
    i = 0

    while i < len(graphs):
        current_graph = graphs[i]

        if ((state := current_graph.state) is not None) and (
            state not in current_graph.chain
        ):
            result.append(current_graph)
            # Remove the finalized graph from the list, avoids `KeyError` exceptions
            # for next iteration.
            graphs.pop(i)

    return result


def _get_proposal_for_single_token(
    symbol_next: Symbol,
    next_terminals_w_history: dict[Symbol, CFGGenerationState],
    finalized_graph: TokenGraph,
) -> dict[Symbol, CFGGenerationState]:
    valid_paths: dict[Symbol, CFGGenerationState] = {}

    # Pass by value, not by reference.
    next_terminals_w_history_copy = deepcopy(next_terminals_w_history)

    if symbol_next.s_type == SymbolType.TERMINAL:
        combination_as_str = finalized_graph._build_string_from_tokens()
        combination_as_symbol = _build_symbol_from_string(
            '"' + combination_as_str + '"'
        )
        combination_as_history = next_terminals_w_history_copy[symbol_next]
        # Give `symbol_next`'s connections to `combination_as_symbol`.
        # [NOTE] Always going to be so, if a symbol exists in `next_terminals_w_history.keys()`
        # then it'll have a history.
        # [NOTE] In case the LLM picks the concatenated symbol,
        # we search for its corresponding symbol, then search for the next connections.
        if combination_as_history:
            combination_as_history[-1].graph.tree[combination_as_symbol] = (
                combination_as_history[-1].graph.tree[symbol_next]
            )
        # Add path.
        valid_paths[combination_as_symbol] = combination_as_history
    else:
        raise CombineError(
            "Expected `SymbolType.TERMINAL` got `{symbol_prev.s_type}` instead."
        )

    return valid_paths


def _update_for_possible_single_token_combinations(
    cfg_guide_object: CFGGuide,
    initial_token_graphs: list[TokenGraph],
) -> dict[Symbol, CFGGenerationState]:
    proposals: dict[Symbol, CFGGenerationState] = {}

    def recurse_update(
        next_terminals_w_history: dict[Symbol, CFGGenerationState],
        next_token_graphs: list[TokenGraph],
        is_head: bool,
    ):
        nonlocal proposals

        # Pass by value, not by reference.
        cfg_guide_object_copy = deepcopy(cfg_guide_object)
        next_terminals_w_history_copy = deepcopy(next_terminals_w_history)

        for symbol_next, hist_next in next_terminals_w_history_copy.items():
            next_token_graphs = _fetch_next_graphs(
                symbol_next.content, next_token_graphs, is_head=is_head
            )

            if next_token_graphs:
                # [NOTE] The finalized graph will be removed from the list, to avoid
                # KeyError exceptions.
                finalized_token_graph = _extract_finalized_graph(next_token_graphs)

                if finalized_token_graph and not is_head:
                    proposal = _get_proposal_for_single_token(
                        symbol_next, next_terminals_w_history, finalized_token_graph[0]
                    )
                    proposals.update(proposal)

                cfg_guide_object_copy.get_next_terminals(hist_next, symbol_next)

                # [NOTE] Control flow deals with case where `next_token_graphs`
                # only contains a finalized graph.
                recurse_update(
                    cfg_guide_object_copy.next_terminals_w_history,
                    next_token_graphs if next_token_graphs else initial_token_graphs,
                    is_head=False,
                )
            else:
                cfg_guide_object_copy.get_next_terminals(hist_next, symbol_next)

                recurse_update(
                    cfg_guide_object_copy.next_terminals_w_history,
                    initial_token_graphs,
                    is_head=True,
                )

    # Get `next_terminals_w_history`.
    next_terminals_w_history = cfg_guide_object.next_terminals_w_history
    # Run.
    recurse_update(next_terminals_w_history, initial_token_graphs, is_head=True)
    # Update `cfg_generation_state`.
    next_terminals_w_history.update(proposals)

    return next_terminals_w_history
