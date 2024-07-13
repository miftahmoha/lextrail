import random
import re
import warnings
from collections import deque
from copy import deepcopy

from cfg_parse.base import OrderedSet, Symbol, SymbolGraph, SymbolType
from cfg_parse.cfg_build.helpers import (
    _get_symbol_predecessors,
    _insert_space_between_delimiters,
)
from cfg_parse.exceptions import (
    InfiniteLoop,
    InvalidGrammar,
    ParsingError,
    SymbolNotFound,
)


def _get_symbol_from_content_attr(
    symbol_graph: SymbolGraph, content: str
) -> list[Symbol]:
    symbols = []

    for symbol_initial in symbol_graph.initials:
        if symbol_initial.content == content:
            symbols.append(symbol_initial)

    for symbol_successors in symbol_graph.tree.values():
        for symbol_successor in symbol_successors:
            if symbol_successor.content == content and symbol_successor not in symbols:
                symbols.append(symbol_successor)

    if len(symbols) == 0:
        raise SymbolNotFound(f"No Symbol matching {content} was found.")

    return symbols


def _is_not_valid_rule_name(rule: str):
    # Special characters REGEX.
    regex = re.compile(r"[@_!#$%^&*()<>?/\\|}~:]")
    return regex.search(rule) is not None


def _split_definition(definition: str):
    return _insert_space_between_delimiters(definition).split()


def _check_for_potential_infinite_loops(
    rule: str, definition: str, symbol_graph: SymbolGraph
):
    is_loop = rule in _split_definition(definition)

    if is_loop:
        warnings.warn(
            f"A potential loop of non-terminal symbols exists in {rule}: {definition}."
        )

        loop_symbols = _get_symbol_from_content_attr(symbol_graph, rule)

        for loop_symbol in loop_symbols:
            if _is_no_escape_from_infinite_loop(symbol_graph, loop_symbol):
                raise InfiniteLoop(
                    f"An infinite loop of non-terminal symbols `{rule} -> {rule}` is found in {rule}: {definition}."
                )


def _divide_cfg_grammar_into_definitions(grammar: str) -> dict[str, str]:
    divided_cfg_grammar_dict: dict[str, str] = {}
    current_rule: str = ""

    lines = grammar.strip().split("\n")

    for line in lines:
        line = line.strip()

        if not line:
            # Skip empty lines.
            continue

        if ":" not in line:
            if not current_rule:
                raise InvalidGrammar(f"Missing `:` in '''{line}'''.")

            divided_cfg_grammar_dict[current_rule] += " " + line

        else:
            parts = line.split(":")

            if len(parts) != 2:
                # Handles multiple use of ':' in a single definition.
                raise InvalidGrammar(f"Invalid grammar rule: {line}.")

            current_rule, definition = parts

            if _is_not_valid_rule_name(current_rule):
                raise InvalidGrammar(f"Invalid rule name: {current_rule}.")

            if current_rule in divided_cfg_grammar_dict:
                raise InvalidGrammar(f"Redefinition of grammar rule: {current_rule}.")

            divided_cfg_grammar_dict[current_rule] = definition.strip()

    if "start" not in divided_cfg_grammar_dict:
        raise InvalidGrammar("The symbol `start` is non-existant.")

    return divided_cfg_grammar_dict


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


def _is_no_escape_from_infinite_loop(symbol_graph: SymbolGraph, symbol_inf: Symbol):
    # Passing by value, not by reference.
    symbol_graph_copy: SymbolGraph = deepcopy(symbol_graph)

    is_no_escape: bool = True

    def _recurse_escape(symbol_graph: SymbolGraph, current_symbol: Symbol):
        nonlocal is_no_escape
        predecessors: OrderedSet = OrderedSet([])

        try:
            predecessors.extend(
                _get_symbol_predecessors(symbol_graph.tree, current_symbol)
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


def _extract_str_from_symbols(symbols: list[Symbol]) -> list[str]:
    symbols_str: list[str] = []

    for symbol in symbols:
        symbols_str.append(symbol.content)

    return symbols_str


def _get_next_terminal_symbols_as_regex(
    symbols: list[Symbol],
) -> str:
    regexes: list[str] = []

    for symbol in symbols:
        if symbol.s_type == SymbolType.TERMINAL:
            regexes.append(re.escape(symbol.content))
        elif symbol.s_type == SymbolType.REGEX:
            regexes.append(symbol.content)
        else:
            raise ParsingError(
                f"{symbol.s_type} is invalid, only {SymbolType.TERMINAL} or {SymbolType.REGEX} are valid."
            )

    return r"(" + r"|".join([r"(" + x + r")" for x in regexes]) + r")"


def _validate_regex(string: str, pattern: str) -> bool:
    regex = re.compile(pattern)
    if regex.fullmatch(string):
        return True
    return False


def _retrace_symbol_obj_from_str(
    chosen_symbol_str: str,
    next_terminal_symbols: list[Symbol],
) -> Symbol:
    chosen_symbols: list[Symbol] = []

    for symbol in next_terminal_symbols:
        # [NOTE] `chosen_symbol_str` could represent more than one symbol in different paths. Send a warning and randomly pick a symbol with equal probability.
        if symbol.s_type == SymbolType.REGEX:
            if _validate_regex(chosen_symbol_str, symbol.content):
                chosen_symbols.append(symbol)
        elif symbol.s_type == SymbolType.TERMINAL:
            if symbol.content == chosen_symbol_str:
                chosen_symbols.append(symbol)
        else:
            raise ParsingError(
                f"{symbol.s_type} is invalid, only {SymbolType.TERMINAL} or {SymbolType.REGEX} are valid."
            )

    # [NOTE] Could be interactive here.
    # Shows the different paths and lets the user choose which one.
    if len(chosen_symbols) > 2:
        warnings.warn(
            "Chosen symbol present in multiple paths, one will be picked with equal probability."
        )
        chosen_symbol = random.choice(chosen_symbols)
        return chosen_symbol

    return chosen_symbols[0]
