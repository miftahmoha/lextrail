import inspect
import re
import warnings
from collections import deque
from copy import deepcopy
from typing import Callable

from lextrail.base import (
    CFGGenerationState,
    OrderedSet,
    Symbol,
    SymbolGraph,
    SymbolType,
)
from lextrail.build.passes import _build_symbol_from_string, _split_symbols
from lextrail.exceptions import InfiniteLoop, InvalidGrammar, SymbolNotFound
from lextrail.helpers import (
    _fetch_non_terminal_from_content_in_graph,
    _fetch_symbol_predecessors_in_tree,
    _is_escaped,
)


def _is_not_valid_rule_name(rule: str):
    # Special characters REGEX.
    regex = re.compile(r"[@_!#$%^&*()<>?/\\|}~:]")
    return regex.search(rule) is not None


def _split_cfg_grammar(grammar: str) -> list[str]:
    in_quote = False
    in_regex = False
    rules: list[str] = []
    current: list[str] = []
    i = 0

    while i < len(grammar):
        current_character = grammar[i]

        if current_character == '"' and not _is_escaped(grammar, i - 1):
            in_quote = not in_quote

        elif current_character == "/" and not in_regex and not in_quote:
            in_regex = not in_regex

        elif current_character == "/" and in_regex:
            in_regex = not in_regex

        elif current_character == "\n" and not in_quote and not in_regex:
            if current:
                rules.append("".join(current))
                current.clear()
            i += 1
            continue

        current.append(current_character)
        i += 1

    return rules


def _divide_cfg_grammar_into_rules(grammar: str) -> dict[str, str]:
    divided_cfg_grammar_dict: dict[str, str] = {}
    current_rule_name: str = ""

    lines = _split_cfg_grammar(grammar)

    for line in lines:
        line = line.strip()

        if not line:
            # Skip empty lines.
            continue

        if ":" not in line:
            # [NOTE] Continued rule in a new line only allowed if `|` is used at the beginning.
            if line[0] != "|":
                raise InvalidGrammar(f"Missing `:` in '''{line}'''.")

            divided_cfg_grammar_dict[current_rule_name] += " " + line

        else:
            parts = line.split(":")

            if len(parts) != 2:
                # Handles multiple use of ':' in a single definition.
                raise InvalidGrammar(f"Invalid grammar rule: {line}.")

            current_rule_name, rule_definition = parts

            if _is_not_valid_rule_name(current_rule_name):
                raise InvalidGrammar(f"Invalid rule name: {current_rule_name}.")

            if current_rule_name in divided_cfg_grammar_dict:
                raise InvalidGrammar(
                    f"Redefinition of grammar rule: {current_rule_name}."
                )

            divided_cfg_grammar_dict[current_rule_name] = rule_definition.strip()

    if "start" not in divided_cfg_grammar_dict:
        raise InvalidGrammar("The symbol `start` is non-existant.")

    return divided_cfg_grammar_dict


"""
    Infinite loops.
"""


def dfs(symbol_graph: SymbolGraph, start: OrderedSet[Symbol]) -> list[Symbol]:
    visited: list[Symbol] = []

    stack = deque()  # type: ignore
    stack.extend(list(start))

    while stack:
        vertex = stack.pop()
        if vertex not in visited:
            visited.append(vertex)
            stack.extend(symbol_graph.tree[vertex])

    return visited


def _check_for_potential_infinite_loops(
    rule_name: str, rule_definition: str, symbol_graph: SymbolGraph
):
    is_loop = rule_name in _split_symbols(rule_definition)

    if is_loop:
        warnings.warn(
            f"A potential loop of non-terminal symbols exists in {rule_name}: {rule_definition}."
        )

        loop_symbols = _fetch_non_terminal_from_content_in_graph(
            symbol_graph, rule_name
        )

        for loop_symbol in loop_symbols:
            if _is_no_escape_from_infinite_loop(symbol_graph, loop_symbol):
                raise InfiniteLoop(
                    f"An infinite loop of non-terminal symbols `{rule_name} -> {rule_name}` is found in {rule_name}: {rule_definition}."
                )


def _is_no_escape_from_infinite_loop(symbol_graph: SymbolGraph, symbol_inf: Symbol):
    # Passing by value, not by reference.
    symbol_graph_copy: SymbolGraph = deepcopy(symbol_graph)

    is_no_escape: bool = True

    def _recurse_escape(symbol_graph: SymbolGraph, current_symbol: Symbol):
        nonlocal is_no_escape
        predecessors: OrderedSet = OrderedSet([])

        try:
            predecessors.extend(
                _fetch_symbol_predecessors_in_tree(symbol_graph.tree, current_symbol)
            )
        except SymbolNotFound:
            # [NOTE] Deals with a case when we reach the beggining of a subgraph,
            # we search if there are some `escapes` in other subgraphs.
            if current_symbol in symbol_graph.initials and current_symbol != symbol_inf:
                predecessors.extend(symbol_graph.initials)
                predecessors.discard(current_symbol)
                visited = dfs(symbol_graph, predecessors)

                if not visited:
                    return

                if symbol_inf not in visited:
                    is_no_escape = False
            else:
                return

        for predecessor in predecessors:
            successors = symbol_graph_copy.tree[predecessor]
            successors.discard(current_symbol)
            visited = dfs(symbol_graph, successors)

            if not visited:
                _recurse_escape(symbol_graph, predecessor)
                continue

            if symbol_inf not in visited:
                is_no_escape = False

    _recurse_escape(symbol_graph_copy, symbol_inf)

    return is_no_escape


"""
    Combining terminals as single tokens as next choice.
"""


def _validate_encoder(encoder: Callable[[str], list[int]]):
    # Get the function's signature.
    signature = inspect.signature(encoder)

    # Check the input parameter.
    params = list(signature.parameters.values())
    if len(params) != 1 or params[0].annotation != str:
        raise TypeError("Encoder must take exactly one string argument.")

    # Check the return type.
    if signature.return_annotation != list[int]:
        raise TypeError("Encoder must return a list of integers.")


def _get_paths_if_valid_single_token(
    symbol_prev: Symbol,
    next_terminals_w_history: dict[Symbol, CFGGenerationState],
    encoder: Callable[[str], list[int]],
) -> dict[Symbol, CFGGenerationState]:
    valid_paths: dict[Symbol, CFGGenerationState] = {}

    # Pass by value, not by reference.
    next_terminals_w_history_copy = deepcopy(next_terminals_w_history)

    for symbol_next in next_terminals_w_history_copy.keys():
        if symbol_next.s_type == SymbolType.TERMINAL:
            str_comb = symbol_prev.content[1:-1] + symbol_next.content[1:-1]
            if len(encoder(str_comb)) == 1:
                symbol_comb = _build_symbol_from_string('"' + str_comb + '"')
                symbol_comb_hist = next_terminals_w_history_copy[symbol_next]
                # Give `symbol_next`'s connections to `symbol_comb`.
                # [NOTE] Always going to be so, if a symbol exists in `next_terminals_w_history.keys()`
                # then it'll have a history.
                if symbol_comb_hist:
                    symbol_comb_hist[-1].graph.tree[symbol_comb] = symbol_comb_hist[
                        -1
                    ].graph.tree[symbol_next]
                # Add path.
                valid_paths[symbol_comb] = symbol_comb_hist

    return valid_paths


# Should be set as some environnemental variable by the user.
def update_for_possible_single_token_combinations(
    cfg_object,
    encoder: Callable[[str], list[int]],
) -> dict[Symbol, CFGGenerationState]:
    proposals: dict[Symbol, CFGGenerationState] = {}

    # [NOTE] Needs better.
    # _validate_encoder(encoder)

    def recurse_update(next_terminals_w_history: dict[Symbol, CFGGenerationState]):
        nonlocal proposals

        # Pass by value, not by reference.
        cfg_object_copy = deepcopy(cfg_object)
        next_terminals_w_history_copy = deepcopy(next_terminals_w_history)

        for symbol_prev, hist_prev in next_terminals_w_history_copy.items():
            cfg_object_copy.get_next_terminals(hist_prev, symbol_prev)
            next_terminals_w_history_out = cfg_object_copy.next_terminals_w_history
            proposal = _get_paths_if_valid_single_token(
                symbol_prev, next_terminals_w_history_out, encoder
            )
            # Search for the next combinations.
            if proposal:
                proposals.update(proposal)
                recurse_update(proposal)

    # Get `next_terminals_w_history`.
    next_terminals_w_history = cfg_object.next_terminals_w_history
    # Run.
    recurse_update(next_terminals_w_history)
    # Update `cfg_generation_state`.
    next_terminals_w_history.update(proposals)

    return next_terminals_w_history
