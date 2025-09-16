import re
import warnings
from collections import deque
from copy import deepcopy

from lextrail.base import Symbol, SymbolGraph
from lextrail.build.passes import _split_symbols
from lextrail.exceptions import InfiniteLoop, InvalidGrammar
from lextrail.helpers import (
    bfs,
    _is_escaped,
)


def _is_not_valid_rule_name(rule: str):
    # Special characters REGEX.
    regex = re.compile(r"[@!#$%^&*()<>?/\\|}~:]")
    return regex.search(rule) is not None


def _split_cfg_grammar(grammar: str) -> list[str]:
    rules = []
    current = []
    in_quote = False
    in_regex = False
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

    if remains := "".join(current).strip():
        rules.append(remains)

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
            # [TODO] Get rid of the RegEx for CF.
            parts = re.split(r"(?<!\"):(?!\")", line)

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


def is_not_escapable_from_infinite_loop(
    symbol_graph: SymbolGraph, loop_content: str
) -> list[Symbol]:
    visited = []
    queue = deque(symbol_graph.initials)

    while queue:
        vertex = queue.popleft()

        # If the vertex is a `infinite` symbol, then it means the (infinite) path is closed.
        if vertex.content == loop_content:
            continue

        # If not, we'll do a DFS/BFS traversal starting at the vertex, it means either
        # (1) there aren't any infinite nodes, thus the path is open and an escape exists,
        # or (2) there are some `infinite` nodes and we can't make a conclusion. In such case,
        # we go to the next nodes and repeat.
        visited_at_vertex = bfs(symbol_graph, [vertex])

        if not any(
            symbol for symbol in visited_at_vertex if symbol.content == loop_content
        ):
            return False

        if vertex not in visited:
            visited.append(vertex)
            queue.extend(symbol_graph.tree[vertex])

    return True


def check_for_potential_infinite_loops(
    rule_name: str, rule_definition: str, symbol_graph: SymbolGraph
):
    is_loop = rule_name in _split_symbols(rule_definition)

    if is_loop:
        warnings.warn(
            f"A potential loop of non-terminal symbols exists in {rule_name}: {rule_definition}."
        )

        if is_not_escapable_from_infinite_loop(symbol_graph, rule_name):
            raise InfiniteLoop(
                f"An infinite loop of non-terminal symbols `{rule_name} -> {rule_name}` is found in {rule_name}: {rule_definition}."
            )
