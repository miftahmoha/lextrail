import os
from collections import defaultdict, deque
from typing import Union

from lextrail.base import OrderedSet, Symbol, SymbolGraph, SymbolType
from lextrail.exceptions import SymbolNotFound


def _is_end_def_symbol(symbol: Symbol) -> bool:
    return symbol.content == "END_DEF" and symbol.s_type == SymbolType.SPECIAL


def _is_end_def_symbol_in_sequence(
    sequence: Union[OrderedSet[Symbol], list[Symbol]],
) -> bool:
    for symbol in sequence:
        if _is_end_def_symbol(symbol):
            return True
    return False


def _fetch_end_def_symbol_in_sequence(
    sequence: Union[OrderedSet[Symbol], list[Symbol]],
) -> list[Symbol]:
    symbols = []
    for symbol in sequence:
        if _is_end_def_symbol(symbol):
            symbols.append(symbol)

    if len(symbols) == 0:
        raise SymbolNotFound("No `END_DEF` symbol was found.")

    return symbols


def _fetch_terminal_from_content_in_sequence(
    sequence: Union[OrderedSet[Symbol], list[Symbol]], content: str
) -> list[Symbol]:
    symbols = []
    for symbol in sequence:
        if symbol.s_type == SymbolType.TERMINAL and symbol.content == content:
            symbols.append(symbol)

    if len(symbols) == 0:
        raise SymbolNotFound(f"No terminal symbol matching {content} was found.")

    return symbols


def _fetch_non_terminal_from_content_in_graph(
    symbol_graph: SymbolGraph, content: str
) -> list[Symbol]:
    symbols = []

    for symbol_initial in symbol_graph.initials:
        if (
            symbol_initial.s_type == SymbolType.NON_TERMINAL
            and symbol_initial.content == content
        ):
            symbols.append(symbol_initial)

    for symbol_successors in symbol_graph.tree.values():
        for symbol_successor in symbol_successors:
            if (
                symbol_successor.s_type == SymbolType.NON_TERMINAL
                and symbol_successor.content == content
                and symbol_successor not in symbols
            ):
                symbols.append(symbol_successor)

    if len(symbols) == 0:
        raise SymbolNotFound(f"No Symbol matching {content} was found.")

    return symbols


def _fetch_symbol_predecessors_in_tree(
    tree: dict[Symbol, OrderedSet[Symbol]], symbol: Symbol
) -> list[Symbol]:
    symbol_predecessors = []
    for symbol_parent, symbol_children in tree.items():
        if symbol in symbol_children:
            symbol_predecessors.append(symbol_parent)

    if len(symbol_predecessors) == 0:
        raise SymbolNotFound(f"No symbol predecessor for {symbol.content} was found.")

    return symbol_predecessors


def _discard_single_nodes_from_tree(
    tree: dict[Symbol, OrderedSet[Symbol]],
) -> dict[Symbol, OrderedSet[Symbol]]:
    tree_copy = tree.copy()

    for symbol_key in tree.keys():
        if not tree[symbol_key]:
            del tree_copy[symbol_key]

    return tree_copy


def _is_escaped(string: str, index: int) -> bool:
    if index < 0:
        return False
    j = 0
    while string[index] == "\\":
        j += 1
        index -= 1
    return j % 2 != 0


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


def bfs(symbol_graph: SymbolGraph, start: OrderedSet[Symbol]) -> list[Symbol]:
    visited = []

    queue = deque()  # type: ignore
    queue.extend(list(start))

    while queue:
        vertex = queue.popleft()
        if vertex not in visited:
            visited.append(vertex)
            queue.extend(symbol_graph.tree[vertex])

    return visited


def _get_symbols_from_generated_symbol_graph(
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


def _extract_content_from_symbols(symbols: list[Symbol]) -> list[str]:
    content: list[str] = []

    for symbol in symbols:
        content.append(symbol.content)

    return content


def _extract_backreference_indices(symbols: list[str]) -> list[int]:
    def _extract_backreference_indices_from_regex(regex: str):
        indices: list[int] = []
        index = ""

        i = 0
        while i < len(regex):
            if (
                regex[i] == "\\"
                and not _is_escaped(regex, i - 1)
                and regex[i + 1].isdigit()
            ):
                i += 1
                while regex[i].isdigit():
                    index += regex[i]
                    i += 1

                indices.append(int(index))
                index = ""

            i += 1

        return indices

    indices: list[int] = []

    for symbol in symbols:
        if symbol.startswith("/") and symbol.endswith("/"):
            indices.extend(_extract_backreference_indices_from_regex(symbol))

    return indices
