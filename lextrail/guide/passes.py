import re
import warnings
from collections import deque

from lextrail.base import SymbolGraph
from lextrail.build.passes import split_definition_into_lexemes
from lextrail.exceptions import InfiniteLoop, InvalidGrammar
from lextrail.helpers import bfs, is_escaped


def _is_not_valid_rule_name(rule: str):
    # Special characters REGEX.
    regex = re.compile(r"[@!#$%^&*()<>?/\\|}~:]")
    return regex.search(rule) is not None


def split_cfg_into_lines(grammar: str) -> list[str]:
    rules: list[str] = []
    in_quote = False
    in_regex = False
    rule: list[str] = []
    i = 0

    while i < len(grammar):
        char = grammar[i]

        if char == '"' and not is_escaped(grammar, i - 1):
            in_quote = not in_quote

        elif char == "/" and not in_regex and not in_quote:
            in_regex = not in_regex

        elif char == "/" and in_regex:
            in_regex = not in_regex

        elif char == "\n" and not in_quote and not in_regex:
            if rule:
                rules.append("".join(rule))
                rule.clear()
            i += 1
            continue

        rule.append(char)
        i += 1

    if remains := "".join(rule).strip():
        rules.append(remains)

    return rules


def divide_cfg_into_rules(grammar: str) -> dict[str, str]:
    divided_cfg: dict[str, str] = {}
    rule_name = ""

    lines = split_cfg_into_lines(grammar)

    for line in lines:
        line = line.strip()

        if not line:
            # Skip empty lines.
            continue

        if ":" not in line:
            # [NOTE] Continued rule in a new line only allowed if `|` is used at the beginning.
            if line[0] != "|":
                raise InvalidGrammar(f"Missing `:` in {line}.")  # noqa: E231

            divided_cfg[rule_name] += " " + line

        else:
            # [TODO] Get rid of the RegEx for CF.
            parts = re.split(r"(?<!\"):(?!\")", line)

            if len(parts) != 2:
                # Handles multiple use of ':' in a single definition.
                raise InvalidGrammar(f"Invalid grammar rule: {line}.")

            rule_name, rule_definition = parts

            if _is_not_valid_rule_name(rule_name):
                raise InvalidGrammar(f"Invalid rule name: {rule_name}.")

            if rule_name in divided_cfg:
                raise InvalidGrammar(f"Redefinition of grammar rule: {rule_name}.")

            divided_cfg[rule_name] = rule_definition.strip()

    if "start" not in divided_cfg:
        raise InvalidGrammar("The symbol `start` is non-existant.")

    return divided_cfg


"""
    Infinite loops.
"""


def is_not_escapable_from_infinite_loop(
    symbol_graph: SymbolGraph, loop_content: str
) -> bool:
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
    is_loop = rule_name in split_definition_into_lexemes(rule_definition)

    if is_loop:
        warnings.warn(
            f"A potential loop of non-terminal symbols exists in {rule_name}: {rule_definition}."
        )

        if is_not_escapable_from_infinite_loop(symbol_graph, rule_name):
            raise InfiniteLoop(
                f"An infinite loop of non-terminal symbols `{rule_name} -> {rule_name}` is found in {rule_name}: {rule_definition}."
            )
