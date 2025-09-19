import os
from collections import defaultdict, deque
from itertools import chain
from typing import Deque

from lextrail.base import Symbol, SymbolGraph, SymbolType
from lextrail.exceptions import SymbolNotFound


def is_end_def_symbol(symbol: Symbol) -> bool:
    return symbol.content == "END_DEF" and symbol.s_type == SymbolType.SPECIAL


def is_escaped(string: str, index: int) -> bool:
    if index < 0:
        return False
    j = 0
    while string[index] == "\\":
        j += 1
        index -= 1
    return j % 2 != 0


def contains_end_def_symbol(symbols: list[Symbol]) -> bool:
    return any(is_end_def_symbol(symbol) for symbol in symbols)


def get_end_def_symbols(symbols: list[Symbol]) -> list[Symbol]:
    symbols = [symbol for symbol in symbols if is_end_def_symbol(symbol)]

    if not symbols:
        raise SymbolNotFound("No `END_DEF` symbol was found.")

    return symbols


def get_terminal_symbols(symbols: list[Symbol], content: str) -> list[Symbol]:
    symbols = [
        symbol
        for symbol in symbols
        if symbol.s_type == SymbolType.TERMINAL and symbol.content == content
    ]

    if len(symbols) == 0:
        raise SymbolNotFound(f"No terminal symbol matching {content} was found.")

    return symbols


def get_symbol_predecessors(
    symbol_tree: dict[Symbol, list[Symbol]], symbol: Symbol
) -> list[Symbol]:
    predecessors = [
        parent for parent, children in symbol_tree.items() if symbol in children
    ]

    if len(predecessors) == 0:
        raise SymbolNotFound(f"No symbol predecessor for {symbol.content} was found.")

    return predecessors


def remove_single_nodes(
    symbol_tree: dict[Symbol, list[Symbol]],
) -> dict[Symbol, list[Symbol]]:
    return defaultdict(list, ((k, v) for k, v in symbol_tree.items() if v))


def bfs(symbol_graph: SymbolGraph, start: list[Symbol]) -> list[Symbol]:
    visited = []

    queue: Deque[Symbol] = deque()
    queue.extend(start)

    while queue:
        vertex = queue.popleft()
        if vertex not in visited:
            visited.append(vertex)
            queue.extend(symbol_graph.tree[vertex])

    return visited


class LTContext:
    def __init__(self, **env):
        self.env = env

    def __enter__(self):
        self.original = {key: os.getenv(key) for key in self.env}
        os.environ.update(self.env)

    def __exit__(self, *args):
        for k, v in self.original.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


"""
    Helper functions for tests.
"""


def get_ordered_symbols_from_symbol_graph(
    symbol_graph: SymbolGraph,
) -> dict[str, Symbol]:
    symbols: dict[str, Symbol] = {}

    start = symbol_graph.initials
    visited = bfs(symbol_graph.copy(), start)

    # The default int is set to 0.
    order: dict[str, int] = defaultdict(int)
    for symbol in visited:
        symbols[symbol.content + f"|{order[symbol.content]}"] = symbol
        order[symbol.content] += 1

    return symbols


def extract_backreference_indices(symbols: list[str]) -> list[int]:
    def get_regex_reference_indices(regex: str):
        indices = []
        i = 0

        while i < len(regex):
            if (
                i + 1 < len(regex)
                and regex[i] == "\\"
                and not is_escaped(regex, i - 1)
                and regex[i + 1].isdigit()
            ):
                i += 1
                start = i

                while regex[i].isdigit():
                    i += 1

                indices.append(int(regex[start:i]))

            i += 1

        return indices

    return list(
        chain.from_iterable(
            get_regex_reference_indices(symbol)
            for symbol in symbols
            if symbol.startswith("/") and symbol.endswith("/")
        )
    )
