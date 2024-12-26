from collections import deque
from copy import deepcopy
from functools import wraps
from typing import Deque, Optional

from lextrail.base import CFGStatefulGraph, Symbol, SymbolGraph, SymbolType
from lextrail.build.build import build_symbol_graph
from lextrail.guide.passes import (
    _check_for_potential_infinite_loops,
    _divide_cfg_grammar_into_rules,
)
from lextrail.helpers import _is_end_def_symbol
from lextrail.exceptions import ParsingError

CFGGenerationState = Optional[Deque[CFGStatefulGraph]]


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


class CFGGuide:
    built_cfg_grammar: dict[str, SymbolGraph]
    next_terminals_w_history: dict[Symbol, CFGGenerationState]

    def __init__(self, cfg_grammar: str):
        self.built_cfg_grammar = build_cfg_grammar_into_symbol_graphs(cfg_grammar)
        self.next_terminals_w_history = {}

    @clear_dict_before_call("next_terminals_w_history")
    def get_next_terminals(
        self,
        generation_state: CFGGenerationState = None,
        chosen_symbol: Optional[Symbol] = None,
    ):
        if generation_state is None:
            if chosen_symbol is None:
                # Turning the symbol graph that'll be added to the stack
                # into a stateful object `CFGStatefulGraph`.
                start = CFGStatefulGraph(self.built_cfg_grammar["start"], "start")
                self.get_next_terminals(generation_state=deque([start]))
                return
            else:
                raise ParsingError(
                    "`CFGGenerationState` is `None` while `chosen_symbol` is not."
                )

        # Poping the last graph.
        last_visit_graph = generation_state[-1].graph

        if chosen_symbol is not None:
            # Get the next nodes according to `chosen_symbol`, which refers to the (terminal) symbol chosen by the LLM.
            next_symbols = last_visit_graph.tree[chosen_symbol]
            # Update the state for `CFGStatefulGraph` to the (terminal) symbol chosen by the LLM.
            generation_state[-1].state = chosen_symbol
        # [NOTE] Sometimes `next_symbols` is returned empty, this can happen when:
        # (1) You pop from the stack, and the place where you land was a `END-OF-DEFINITON`
        # non-terminal symbol (we return a `None` chosen symbol after poping from the stack).
        # (2) The second case where we pass a `chosen_symbol = None` is at the beggining.
        # Thus, the following will be executed if `start` is connected to one single terminal symbol.
        # Handles reaching the end of a symbol graph (`next_symbols` being empty).
        else:
            last_visit_symbol = generation_state[-1].state
            next_symbols = (
                last_visit_graph.tree[last_visit_symbol]
                if last_visit_symbol is not None
                else last_visit_graph.initials
            )

        # Handles reaching the end of a symbol graph (`next_symbols` being empty).
        if not next_symbols:
            generation_state.pop()
            # Handles reaching the end of stack.
            if not generation_state:
                return
            # Should return the last label, but as a symbol of the last symbol graph.
            self.get_next_terminals(deepcopy(generation_state))
            return

        for next_symbol in next_symbols:
            if next_symbol.s_type in [
                SymbolType.TERMINAL,
                SymbolType.REGEX,
            ] or _is_end_def_symbol(next_symbol):
                # Pass by value, not by reference.
                updated_generation_state = deepcopy(generation_state)
                # Set state to the last visited symbol.
                updated_generation_state[-1].state = next_symbol
                # Save the next possible terminal `next_symbol` with its history.
                self.next_terminals_w_history[next_symbol] = updated_generation_state

            # Create an additional layer in the stack.
            if next_symbol.s_type == SymbolType.NON_TERMINAL:
                # Pass by value, not by reference.
                updated_generation_state = deepcopy(generation_state)
                # Set up the state for the bottom stack layer, it'll save where we left for when
                # we pop the upper stack layer. We would then search for the next symbols from
                # the last visited `non-terminal` symbol.
                updated_generation_state[-1].state = next_symbol
                # Turning the symbol graph that'll be added to the stack
                # into a stateful object `CFGStatefulGraph`.
                cfg_stateful_graph = CFGStatefulGraph(
                    graph=self.built_cfg_grammar[next_symbol.content],
                    label=next_symbol.content,
                )
                # Adding the stateful graph layer to the stack.
                updated_generation_state.append(cfg_stateful_graph)
                # Recurse over the added layer.
                self.get_next_terminals(updated_generation_state)
