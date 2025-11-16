import os
from collections import defaultdict, deque
from itertools import chain
from typing import Deque

from lextrail.base import Symbol, Symbol_Kind, SymbolGraph


def is_end_def_symbol(symbol: Symbol) -> bool:
    return symbol.content == "END" and symbol.kind == Symbol_Kind.END


def is_escaped(string: str, index: int) -> bool:
    if index < 0:
        return False
    j = 0
    while string[index] == "\\":
        j += 1
        index -= 1
    return j % 2 != 0


def remove_single_nodes(
    symbol_tree: dict[Symbol, list[Symbol]],
) -> dict[Symbol, list[Symbol]]:
    return defaultdict(list, ((k, v) for k, v in symbol_tree.items() if v))


def safe_node_connect(tree: dict[Symbol, list[Symbol]], from_: Symbol, to_: Symbol):
    tree[from_] += (
        [to_] if to_ not in tree[from_] and not is_end_def_symbol(from_) else []
    )


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


class TrailContext:
    def __init__(self, **env):
        self.env = env

    def __enter__(self):
        self.original = {key: os.getenv(key) for key in self.env}
        os.environ.update(self.env)

    def __exit__(self, *args):
        for k, v in self.original.items():
            if v is None:
                del os.environ[k]
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
        content = (
            f'"{symbol.content}"'
            if symbol.kind == Symbol_Kind.TERMINAL
            else symbol.content
        )
        symbols[content + f"|{order[content]}"] = symbol
        order[content] += 1

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
