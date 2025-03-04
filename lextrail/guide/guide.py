from collections import defaultdict, deque
from copy import deepcopy
from functools import wraps
from typing import Deque

from lextrail.base import (
    CFGGenerationState,
    CFGStatefulGraph,
    Symbol,
    SymbolGraph,
    SymbolType,
)
from lextrail.build.build import build_symbol_graph
from lextrail.exceptions import ParsingError
from lextrail.guide.passes import (
    _check_for_potential_infinite_loops,
    _divide_cfg_grammar_into_rules,
)
from lextrail.helpers import _is_end_def_symbol


def build_cfg_grammar_into_symbol_graphs(cfg_grammar: str) -> dict[str, SymbolGraph]:
    built_cfg_grammar_dict: dict[str, SymbolGraph] = {}

    divided_cfg_grammar_dict = _divide_cfg_grammar_into_rules(cfg_grammar)

    for symbol_name, symbol_def in divided_cfg_grammar_dict.items():
        built_cfg_grammar_dict[symbol_name] = build_symbol_graph(symbol_def)

        # [NOTE] Check for potential infinite loops in the CFG.
        # (1) WARNING: There is an infinite loop but there exists a path to escape to it.
        # (2) EXCEPTION: There is an infinite loop but there is no escape.
        _check_for_potential_infinite_loops(
            symbol_name, symbol_def, built_cfg_grammar_dict[symbol_name]
        )

    return built_cfg_grammar_dict


def clear_dict_before_call(dict_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            getattr(self, dict_name).clear()
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


class Guide:
    built_symbol_graph: SymbolGraph
    next_terminals_w_history: dict[Symbol, CFGStatefulGraph]
    backreferences: dict[int, str]

    def __init__(self, definition: str):
        self.built_symbol_graph = build_symbol_graph(definition)
        self.next_terminals_w_history = {}
        self.backreferences = defaultdict(str)

    def backreference(self, chosen_symbols: list[Symbol]):
        def extract_indices(start_key, dictionary):
            result = [start_key]
            current_key = start_key

            # Start with value one less than initial.
            current_value = dictionary[start_key] - 1

            while current_value >= 1:
                # Find largest key less than current_key with current_value.
                next_key = max(
                    (
                        k
                        for k in dictionary.keys()
                        if k < current_key and dictionary[k] == current_value
                    ),
                    default=None,
                )

                if next_key is None:
                    break

                result.append(next_key)
                current_key = next_key
                # Decrease the value we're looking for.
                current_value -= 1

            return result

        # Content of the symbols must be the same.
        if not all(x == chosen_symbols[0] for x in chosen_symbols):
            raise ParsingError("Ambiguous symbols must have same content.")

        chosen_symbol = chosen_symbols[0]

        count = chosen_symbol.s_metadata["_DEPTH"]

        indices = extract_indices(
            count, self.built_symbol_graph.metadata["_COUNT_TO_DEPTH"]
        )

        for index in indices:
            self.backreferences[index] += chosen_symbol.content[1:-1]

    @clear_dict_before_call("next_terminals_w_history")
    def get_next_terminals(
        self,
        chosen_symbols: list[Symbol] = [],
        chosen_states: list[CFGStatefulGraph] = [],
    ):
        if isinstance(chosen_symbols, Symbol):
            chosen_symbols = [chosen_symbols]

        if isinstance(chosen_states, CFGStatefulGraph):
            chosen_states = [chosen_states]

        if not chosen_states:
            if not chosen_symbols:
                # Turning the symbol graph that'll be added to the stack
                # into a stateful object `CFGStatefulGraph`.
                start = CFGStatefulGraph(self.built_symbol_graph, "start")
                self.get_next_terminals(chosen_states=[start])
                return
            else:
                raise ParsingError(
                    "`CFGGenerationState` is empty while `chosen_symbols` is not."
                )

        # Poping the last graphs.
        last_visit_graphs = [chosen_state.graph for chosen_state in chosen_states]

        if chosen_symbols:
            # Backreference update.
            self.backreference(chosen_symbols)
            # Update the state for `CFGStatefulGraph` to the terminal(s) symbol(s) chosen by the LLM.
            for chosen_state, chosen_symbol in zip(chosen_states, chosen_symbols):
                chosen_state.state = chosen_symbol
            # Get the next sequences.
            next_sequences = [
                last_visit_graph.tree[chosen_symbol]
                for last_visit_graph, chosen_symbol in zip(
                    last_visit_graphs, chosen_symbols
                )
            ]
        # [NOTE] Sometimes `next_symbols` is returned empty, this can happen when:
        # (1) You pop from the stack, and the place where you land was a `END-OF-DEFINITON`
        # non-terminal symbol (we return a `None` chosen symbol after popping from the stack).
        # (2) The second case where we pass a `chosen_symbols = None` is at the beginning.
        # Thus, the following will be executed if `start` is connected to one single terminal symbol.
        # Handles reaching the end of a symbol graph (`next_symbols` being empty).
        else:
            # `last_visit_symbol` will be None at the beginning of the process, otherwise it'll have a valid state.
            last_visit_symbols = [chosen_state.state for chosen_state in chosen_states]
            # Get the next sequences.
            next_sequences = [
                (
                    last_visit_graph.tree[last_visit_symbol]
                    if last_visit_symbol is not None
                    else last_visit_graph.initials
                )
                for last_visit_graph, last_visit_symbol in zip(
                    last_visit_graphs, last_visit_symbols
                )
            ]

        # Handles reaching the end of a symbol graph (`next_symbols` being empty).
        for next_symbols, chosen_state in zip(next_sequences, chosen_states):
            if not next_symbols:
                return

        for next_symbols, chosen_state in zip(next_sequences, chosen_states):
            for next_symbol in next_symbols:
                if next_symbol.s_type in [
                    SymbolType.TERMINAL,
                    SymbolType.REGEX,
                    SymbolType.NON_TERMINAL,
                ] or _is_end_def_symbol(next_symbol):
                    # Pass by value, not by reference.
                    next_chosen_state = deepcopy(chosen_state)
                    # Set state to the last visited symbol.
                    next_chosen_state.state = next_symbol
                    # Save the next possible terminal `next_symbol` with its history.
                    self.next_terminals_w_history[next_symbol] = next_chosen_state
                elif next_symbol.s_type == SymbolType.REFERENCE:
                    # Backreference successors should be unique.
                    if len(next_symbols) > 1:
                        raise ParsingError("Reference successor is not unique.")
                    # Retrieve index.
                    index = int(next_symbol.content[1:])
                    # Check if index is valid.
                    if index not in self.backreferences.keys():
                        raise ParsingError(f"Invalid backreference <\\{index}>.")
                    # Modify the REFERENCE symbol into a TERMINAL symbol with the corresponding content.
                    next_symbol.s_type, next_symbol.content = (
                        SymbolType.TERMINAL,
                        f'"{self.backreferences[index-1]}"',
                    )
                    self.next_terminals_w_history[next_symbol] = chosen_state


class CFGGuide:
    built_cfg_grammar: dict[str, SymbolGraph]
    next_terminals_w_history: dict[Symbol, Deque[CFGStatefulGraph]]
    backreferences: dict[str, dict[int, str]]

    def __init__(self, cfg_grammar: str):
        self.built_cfg_grammar = build_cfg_grammar_into_symbol_graphs(cfg_grammar)
        self.next_terminals_w_history = {}
        self.backreferences = defaultdict(lambda: defaultdict(str))

    def backreference(self, chosen_symbols: list[Symbol], chosen_states: list[CFGGenerationState]):
        def extract_indices(start_key, dictionary):
            result = [start_key]
            current_key = start_key

            # Start with value one less than initial.
            current_value = dictionary[start_key] - 1

            while current_value >= 1:
                # Find largest key less than current_key with current_value.
                next_key = max(
                    (
                        k
                        for k in dictionary.keys()
                        if k < current_key and dictionary[k] == current_value
                    ),
                    default=None,
                )

                if next_key is None:
                    break

                result.append(next_key)
                current_key = next_key
                # Decrease the value we're looking for.
                current_value -= 1

            return result

        # Content and state of the symbols must be the same.
        if not all(x == chosen_symbols[0] for x in chosen_symbols) or not all(x == chosen_states[0] for x in chosen_states):
            raise ParsingError("Ambiguous symbols must have identical content and state.")

        chosen_symbol, chosen_state = chosen_symbols[0], chosen_states[0]

        label = chosen_state[-1].label 
 
        count = chosen_symbol.s_metadata["_DEPTH"]

        indices = extract_indices(
            count, self.built_cfg_grammar[label].metadata["_COUNT_TO_DEPTH"]
        )

        for index in indices:
            self.backreferences[label][index] += chosen_symbol.content[1:-1]

        # Propagating backreferences into lower layers.
        for layer in list(chosen_state)[:-1]:
            state_symbol, state_label = layer.state, layer.label

            assert layer.state is not None, "None state was found while backreferencing."

            count = state_symbol.s_metadata["_DEPTH"] # type: ignore

            indices = extract_indices(
                count, self.built_cfg_grammar[state_label].metadata["_COUNT_TO_DEPTH"]
            )
            
            for index in indices:
                self.backreferences[state_label][index] += chosen_symbol.content[1:-1]

    @clear_dict_before_call("next_terminals_w_history")
    def get_next_terminals(
        self,
        chosen_symbols: list[Symbol] = [],
        chosen_states: list[CFGGenerationState] = [],
    ):
        if isinstance(chosen_symbols, Symbol):
            chosen_symbols = [chosen_symbols]

        if isinstance(chosen_states, Deque) and all(
            isinstance(x, CFGStatefulGraph) for x in chosen_states
        ):
            chosen_states = [chosen_states]

        if not chosen_states:
            if not chosen_symbols:
                # Turning the symbol graph that'll be added to the stack
                # into a stateful object `CFGStatefulGraph`.
                start = CFGStatefulGraph(self.built_cfg_grammar["start"], "start")
                self.get_next_terminals(chosen_states=[deque([start])])
                return
            else:
                raise ParsingError(
                    "`CFGGenerationState` is empty while `chosen_symbols` is not."
                )

        # Poping the last graphs.
        last_visit_graphs = [chosen_state[-1].graph for chosen_state in chosen_states]

        if chosen_symbols:
            # Backreference update.
            # Ambiguous symbols must have same content and (same)? label.
            self.backreference(chosen_symbols, chosen_states)
            # Update the state for `CFGStatefulGraph` to the terminal(s) symbol(s) chosen by the LLM.
            for chosen_state, chosen_symbol in zip(chosen_states, chosen_symbols):
                chosen_state[-1].state = chosen_symbol
            # Get the next sequences.
            next_sequences = [
                last_visit_graph.tree[chosen_symbol]
                for last_visit_graph, chosen_symbol in zip(
                    last_visit_graphs, chosen_symbols
                )
            ]
        # [NOTE] Sometimes `next_symbols` is returned empty, this can happen when:
        # (1) You pop from the stack, and the place where you land was a `END-OF-DEFINITON`
        # non-terminal symbol (we return a `None` chosen symbol after popping from the stack).
        # (2) The second case where we pass a `chosen_symbols = []` is at the beginning.
        # Thus, the following will be executed if `start` is connected to one single terminal symbol.
        # Handles reaching the end of a symbol graph (`next_symbols` being empty).
        else:
            # `last_visit_symbol` will be None at the beginning of the process, otherwise it'll have a valid state.
            last_visit_symbols = [
                chosen_state[-1].state for chosen_state in chosen_states
            ]
            # Get the next sequences.
            next_sequences = [
                (
                    last_visit_graph.tree[last_visit_symbol]
                    if last_visit_symbol is not None
                    else last_visit_graph.initials
                )
                for last_visit_graph, last_visit_symbol in zip(
                    last_visit_graphs, last_visit_symbols
                )
            ]

        # Handles reaching the end of a symbol graph (`next_symbols` being empty).
        for next_symbols, chosen_state in zip(next_sequences, chosen_states):
            if not next_symbols:
                chosen_state.pop()
                # Handles reaching the end of stack.
                if not chosen_state:
                    return
                # Should return the last label, but as a symbol of the last symbol graph.
                self.get_next_terminals(chosen_states=[deepcopy(chosen_state)])
                return

        for next_symbols, chosen_state in zip(next_sequences, chosen_states):
            for next_symbol in next_symbols:
                if next_symbol.s_type in [
                    SymbolType.TERMINAL,
                    SymbolType.REGEX,
                ] or _is_end_def_symbol(next_symbol):
                    # Pass by value, not by reference.
                    next_chosen_state = deepcopy(chosen_state)
                    # Set state to the last visited symbol.
                    next_chosen_state[-1].state = next_symbol
                    # Save the next possible terminal `next_symbol` with its history.
                    self.next_terminals_w_history[next_symbol] = next_chosen_state

                # Create an additional layer in the stack.
                if next_symbol.s_type == SymbolType.NON_TERMINAL:
                    # Pass by value, not by reference.
                    next_chosen_state = deepcopy(chosen_state)
                    # Set up the state for the bottom stack layer, it'll save where we left for when
                    # we pop the upper stack layer. We would then search for the next symbols from
                    # the last visited `non-terminal` symbol.
                    next_chosen_state[-1].state = next_symbol
                    # Turning the symbol graph that'll be added to the stack
                    # into a stateful object `CFGStatefulGraph`.
                    cfg_stateful_graph = CFGStatefulGraph(
                        graph=self.built_cfg_grammar[next_symbol.content],
                        label=next_symbol.content,
                    )
                    # Adding the stateful graph layer to the stack.
                    next_chosen_state.append(cfg_stateful_graph)
                    # Recurse over the added layer.
                    self.get_next_terminals(chosen_states=[next_chosen_state])

                if next_symbol.s_type == SymbolType.REFERENCE:
                    # Backreference successors should be unique.
                    if len(next_symbols) > 1:
                        raise ParsingError("Reference successor is not unique.")
                    # Retrieve index.
                    index = int(next_symbol.content[1:])
                    # Check if index is valid.
                    if (
                        index
                        not in self.backreferences[chosen_states[0][-1].label].keys()
                    ):
                        raise ParsingError(f"Invalid backreference <\\{index}>.")
                    # Modify the REFERENCE symbol into a TERMINAL symbol with the corresponding content.
                    next_symbol.s_type, next_symbol.content = (
                        SymbolType.TERMINAL,
                        f'"{self.backreferences[chosen_states[0][-1].label][index-1]}"',
                    )
                    self.next_terminals_w_history[next_symbol] = chosen_state
