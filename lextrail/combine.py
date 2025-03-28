import uuid
from dataclasses import dataclass, field

from lextrail.base import CFGGenerationState, CFGStatefulGraph, Symbol, SymbolType
from lextrail.build.passes import _build_symbol_from_string
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
    state: TokenNode | None = None

    @property
    def content(self):
        # Returns the accumulated content until the state.
        if self.state is None:
            raise CombineError("Access to a string while state set to None.")
        out_as_str = ""
        out_as_tok = self.head
        while out_as_tok != self.state:
            out_as_str += out_as_tok.content
            out_as_tok = self.chain[out_as_tok]
        out_as_str += out_as_tok.content
        return out_as_str

    def __eq__(self, other) -> bool:
        if isinstance(other, TokenGraph):
            return (self.head == other.head) and (self.chain == other.chain)
        return NotImplemented

    def __bool__(self) -> bool:
        return bool(self.head) and bool(self.chain)

    def copy(self):
        return TokenGraph(
            chain=self.chain.copy(),
            head=self.head,
            state=self.state,
        )


def _build_token_graphs(vocabulary: list[str]) -> list[TokenGraph]:
    graphs: list[TokenGraph] = []

    for word in vocabulary:
        chain: dict[TokenNode, TokenNode] = {}
        previous: TokenNode | None = None

        for character in list(word):
            if previous:
                next = TokenNode(character)
                chain[previous] = next
                previous = next
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
        raise CombineError("Can't fetch for next graphs, array is empty.")

    if is_head:
        for graph in graphs:
            if (head := graph.head).content == next_terminal[
                1:-1
            ]:  # Removing the `<">..<">` from terminals.
                next_graph = graph.copy()
                next_graph.state = head
                result.append(next_graph)
    else:
        for graph in graphs:
            if graph.chain[graph.state].content == next_terminal[1:-1]:  # type: ignore
                next_graph = graph.copy()
                next_graph.state = graph.chain[graph.state]  # type: ignore
                result.append(next_graph)

    return result


def _fetch_completed_graph(graphs: list[TokenGraph]) -> list[TokenGraph]:
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

        i += 1

    return result


def _extract_single_token_proposal(
    symbol_next: Symbol,
    next_terminals_w_states: dict[Symbol, CFGGenerationState],
    completed_graph: TokenGraph,
) -> dict[Symbol, CFGGenerationState]:
    valid_paths: dict[Symbol, CFGGenerationState] = {}

    if symbol_next.s_type == SymbolType.TERMINAL:
        combination_symbol = _build_symbol_from_string(
            '"' + completed_graph.content + '"'
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
    graphs: list[TokenGraph],
):
    proposals: dict[Symbol, CFGStatefulGraph | CFGGenerationState] = {}

    def recurse_update(
        next_terminals_w_states: dict[Symbol, CFGGenerationState],
        next_token_graphs: list[TokenGraph],
        is_head: bool,
    ):
        nonlocal proposals

        for symbol_next, state_next in next_terminals_w_states.items():
            current_next_token_graphs = _fetch_next_graphs(
                symbol_next.content, next_token_graphs, is_head=is_head
            )

            if current_next_token_graphs:
                # [NOTE] The finalized graph will be removed from
                # the `current_next_token_graphs`, to avoid KeyError in the next iteration.
                finalized_token_graph = _fetch_completed_graph(
                    current_next_token_graphs
                )

                if finalized_token_graph and not is_head:
                    proposal = _extract_single_token_proposal(
                        symbol_next, next_terminals_w_states, finalized_token_graph[0]
                    )
                    proposals.update(proposal)

                # [NOTE] Control flow deals with the case where `current_next_token_graphs` does
                # only contain a finalized graph.
                if len(current_next_token_graphs) == 0:
                    continue

                guide._get_next_terminals([symbol_next], [state_next])

                recurse_update(
                    guide._next_terminals_w_states.copy(),
                    current_next_token_graphs,
                    is_head=False,
                )
            else:
                continue

    # Get `next_terminals_w_states`.
    next_terminals_w_states = guide._next_terminals_w_states.copy()
    # Run.
    recurse_update(next_terminals_w_states, graphs, is_head=True)
    # Update `cfg_generation_state`.
    next_terminals_w_states.update(proposals)

    return next_terminals_w_states
