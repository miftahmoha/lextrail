import re
from collections import defaultdict, deque
from typing import Deque

from cfg_parse.base import OrderedSet, Symbol, SymbolGraph, SymbolType
from cfg_parse.exceptions import (
    InvalidDelimiters,
    InvalidSymbol,
    MissingQuote,
    SymbolNotFound,
)


def _convert_str_to_symbol(symbol_str: str) -> Symbol:
    if symbol_str.startswith('"') and symbol_str.endswith('"'):
        node = Symbol(symbol_str, SymbolType.TERMINAL)

    elif symbol_str.startswith('regex("') and symbol_str.endswith('")'):
        # Index to strip `symbol` from `regex()`.
        start = symbol_str.find("(")
        # [NOTE] Use a raw string.
        node = Symbol(symbol_str[start + 1 : -1], SymbolType.REGEX)

    elif symbol_str in ("(", ")", "[", "]", "{", "}"):
        node = Symbol(symbol_str, SymbolType.SPECIAL)

    else:
        node = Symbol(symbol_str, SymbolType.NON_TERMINAL)

    return node


def _get_symbol_predecessors(
    symbol_graph_tree: dict[Symbol, OrderedSet[Symbol]], search_symbol: Symbol
) -> list[Symbol]:
    symbol_predecessors = []
    for symbol_parent, symbol_children in symbol_graph_tree.items():
        if search_symbol in symbol_children:
            symbol_predecessors.append(symbol_parent)

    if len(symbol_predecessors) == 0:
        raise SymbolNotFound(
            f"No Symbol predecessor for {search_symbol.content} was found."
        )

    return symbol_predecessors


def _is_end_def_symbol(symbol: Symbol):
    return symbol.content == "END_DEF" and symbol.s_type == SymbolType.SPECIAL


def _is_set_contains_end_def_symbol(ordered_set: OrderedSet[Symbol]) -> bool:
    for symbol in ordered_set:
        if _is_end_def_symbol(symbol):
            return True
    return False


def _get_end_def_symbol_for_seq(
    sequence: OrderedSet[Symbol] | list[Symbol],
) -> list[Symbol]:
    symbols = []
    for symbol in sequence:
        if _is_end_def_symbol(symbol):
            symbols.append(symbol)

    if len(symbols) == 0:
        raise SymbolNotFound(f"No Symbol matching {content} was found.")

    return symbols


def _discard_single_nodes_from_tree(
    symbol_graph_tree: dict[Symbol, OrderedSet[Symbol]]
) -> dict[Symbol, OrderedSet[Symbol]]:
    single_node_symbols = []
    symbol_graph_tree_copy = symbol_graph_tree.copy()

    # [NOTE] The reason we can't delete directly is
    # `RuntimeError: dictionary changed size during iteration`.
    for symbol_key in symbol_graph_tree_copy.keys():
        if not symbol_graph_tree_copy[symbol_key]:
            single_node_symbols.append(symbol_key)

    for single_node_symbol in single_node_symbols:
        del symbol_graph_tree_copy[single_node_symbol]

    return symbol_graph_tree_copy


# [NOTE] Make it accessible only for terminals.
def _get_symbol_from_content_attr_for_seq(
    sequence: OrderedSet[Symbol] | list[Symbol], content: str
) -> list[Symbol]:
    symbols = []
    for symbol in sequence:
        if symbol.content == content:
            symbols.append(symbol)

    if len(symbols) == 0:
        raise SymbolNotFound(f"No Symbol matching {content} was found.")

    return symbols


def _get_once_initial_for_none_any_or_once_end_def_symbols(symbol_graph: SymbolGraph):
    symbols: list[Symbol] = []
    single_symbols: list[Symbol] = []

    for symbol_initial in symbol_graph.initials:
        if _is_end_def_symbol(symbol_initial):
            single_symbols.append(symbol_initial)

    for symbol_successors in symbol_graph.tree.values():
        for symbol_successor in symbol_successors:
            if _is_end_def_symbol(
                symbol_successor
            ) and symbol_successor not in symbols + list(symbol_graph.finals):
                symbols.append(symbol_successor)
    return symbols, single_symbols


# Throws exception if delimiters are invalid.
def _check_for_delimiter_coherence(symbol_def_str: list[str]):
    stack_delim_tracker: Deque[tuple[int, str]] = deque()

    # We capture the index to send useful error messages.
    for symbol_index, symbol_str in enumerate(symbol_def_str):
        if symbol_str in ["(", "[", "{"]:
            stack_delim_tracker.append((symbol_index, symbol_str))

        elif symbol_str == ")":
            if not stack_delim_tracker or stack_delim_tracker[-1][1] != "(":
                raise InvalidDelimiters(
                    f'No opening delimiter `(` found for `)` in `{" ".join(symbol_def_str[:symbol_index])} <<{symbol_def_str[symbol_index]}>>`.'
                )
            stack_delim_tracker.pop()

        elif symbol_str == "}":
            if not stack_delim_tracker or stack_delim_tracker[-1][1] != "{":
                raise InvalidDelimiters(
                    f'No opening delimiter {"`{`"} found for {"`}`"} in `{" ".join(symbol_def_str[:symbol_index])} <<{symbol_def_str[symbol_index]}>>`.'
                )
            stack_delim_tracker.pop()

        elif symbol_str == "]":
            if not stack_delim_tracker or stack_delim_tracker[-1][1] != "[":
                raise InvalidDelimiters(
                    f'No opening delimiter `[` found for `]` in `{" ".join(symbol_def_str[:symbol_index])} <<{symbol_def_str[symbol_index]}>>`.'
                )
            stack_delim_tracker.pop()

    # Raise an exception if the stack is not empty.
    if stack_delim_tracker:
        symbol_index, symbol_str = stack_delim_tracker[-1]
        raise InvalidDelimiters(
            f'Non enclosed delimiter `{symbol_str}` in `{" ".join(symbol_def_str[:symbol_index+1])}`.'
        )


def _is_valid_symbol_syntax(symbol_str: str) -> bool:
    # Special characters REGEX.
    regex = re.compile(r"[@_!#$%^&*()<>?/\\|}~:]")

    def _is_terminal(symbol_str: str):
        return symbol_str[0] == '"' and symbol_str[-1] == '"'

    def _is_non_terminal(symbol_str: str):
        return (
            symbol_str[0] != '"'
            and symbol_str[-1] != '"'
            and (regex.search(symbol_str) is None)
        )

    def _is_regex(symbol_str: str):
        return symbol_str.startswith('regex("') and symbol_str.endswith('")')

    def _is_special_symbol(symbol_str: str):
        return symbol_str in "()[]{}<>|*+?" and len(symbol_str) == 1

    return (
        _is_terminal(symbol_str)
        or _is_non_terminal(symbol_str)
        or _is_regex(symbol_str)
        or _is_special_symbol(symbol_str)
    )


# This checks if the symbol's syntax is correct.
def _check_symbol_syntax(symbol_def_str: list[str]):
    for symbol_str in symbol_def_str:
        # 1) Check for symbol validity.
        if not _is_valid_symbol_syntax(symbol_str):
            raise InvalidSymbol(f"Invalid symbol name {symbol_str}.")


# This checks if the definition is correct.
def _check_for_errors_symbol_def(symbol_def_str: list[str]):
    # [NOTE] Needs tests.
    _check_symbol_syntax(symbol_def_str)
    _check_for_delimiter_coherence(symbol_def_str)


# [DEPRACATED] Need additional initial `( )` for `build_full_graph` to start.
def _insert_standard_delimiters(symbol_def: str):
    return "(" + symbol_def + ")"


# [DEPRACATED] Insert space between delimiters, `terminal` delimiters `"(", ")", "[", "]", "{", "}"` are not considered.
def _insert_space_between_delimiters(symbol_def_str: str) -> str:
    in_quote = False
    in_regex = False
    result = []
    i = 0

    while i < len(symbol_def_str):
        if symbol_def_str[i] == '"' and not in_regex:
            in_quote = not in_quote
            result.append(symbol_def_str[i])

        elif symbol_def_str[i : i + 5] == "regex":
            in_regex = True
            result.append(symbol_def_str[i])

        elif symbol_def_str[i] in "([{" and not in_quote and not in_regex:
            result.append(" " + symbol_def_str[i] + " ")

        elif symbol_def_str[i] in ")]}" and not in_quote and not in_regex:
            result.append(" " + symbol_def_str[i] + " ")

        elif symbol_def_str[i] == ")" and in_regex:
            in_regex = False
            result.append(symbol_def_str[i])

        else:
            result.append(symbol_def_str[i])
        i += 1

    return "".join(result)


# [DEPRACATED]
def _pre_process_symbol_def(symbol_def: str) -> str:
    return _insert_space_between_delimiters(_insert_standard_delimiters(symbol_def))


def _is_escaped(regex_str: str, index: int) -> bool:
    if index < 0:
        return False
    j = 0
    while regex_str[index] == "\\":
        j += 1
        index -= 1
    return j % 2 != 0


def _check_if_valid_regex(pattern):
    try:
        re.compile(pattern)
        return True
    except re.error:
        raise InvalidSymbol(f"The regex expression {pattern} is invalid.")


def _split_symbols(symbol_def_str: str) -> list[str]:
    in_quote = False
    in_regex = False
    is_escaped_quote = False
    is_regex_delim = False
    result = []
    current = []
    i = 0

    while i < len(symbol_def_str):
        current_character = symbol_def_str[i]

        # Dealing with REGEX expressions.
        if symbol_def_str[i - 5 : i + 2] == 'regex("':
            current.append(current_character)
            in_regex = not in_regex

        elif symbol_def_str[i - 1 : i + 1] == '")' and in_regex and not is_regex_delim:
            result.append("".join(current) + current_character)
            current.clear()
            in_regex = not in_regex

        # Special case: Dealing with an escaped quote "\"".
        # `"` is used as symbol delimiters for terminals (`"<symbol_name>"`), but for the user to express `"`
        # as a terminal, he/she needs to escape it as follows "\"".
        elif (
            current_character == "\\"
            and not _is_escaped(symbol_def_str, i - 1)
            and symbol_def_str[i + 1] == '"'
            and in_quote
        ):
            is_escaped_quote = not is_escaped_quote

        # Converting ()*, ()+ and ()? syntax to standard.
        elif (
            current_character == ")"
            and i + 1 < len(symbol_def_str)
            and symbol_def_str[i + 1] in "+*?"
            and not in_quote
            and not in_regex
        ):
            i_dict: dict[str, str] = {"*": "{", "+": "<", "?": "["}
            o_dict: dict[str, str] = {"*": "}", "+": ">", "?": "]"}
            if current:
                result.append("".join(current))
                current.clear()
            # Convert `*+?` to standard `)]}`.
            result.append(o_dict[symbol_def_str[i + 1]])
            # Convert `*+?` to standard `([{`.
            for idx in reversed(range(len(result))):
                if result[idx] == "(":
                    result[idx] = i_dict[symbol_def_str[i + 1]]
                    break
            # Jump over `*+?`.
            i += 2
            continue

        # Dealing with special delimiters.
        elif current_character in "()[]{}<>" and not in_quote and not in_regex:
            # Separating delimiters from non-terminal symbols.
            if current:
                result.append("".join(current))
                current.clear()
            result.append(current_character)

        elif current_character == '"':
            if in_regex:
                current.append('"')
                i += 1
                continue
            elif is_escaped_quote:
                current.append('"')
                is_escaped_quote = not is_escaped_quote
                i += 1
                continue
            elif in_quote:
                current.append('"')
                result.append("".join(current))
                current.clear()
            else:
                if current:
                    result.append("".join(current))
                    current.clear()
                current.append(current_character)
            in_quote = not in_quote

        elif current_character.isspace():
            if not in_quote and not in_regex:
                if current:
                    result.append("".join(current))
                    current.clear()
            else:
                current.append(current_character)

        else:
            current.append(current_character)

        i += 1

    if current:
        result.append("".join(current))

    if in_quote:
        raise MissingQuote(
            'Quote `"` is missing, terminals should be expressed as "<terminal_name>".'
        )

    return result


def _convert_str_def_to_str_queue(symbol_def: str) -> Deque[str]:
    symbols = _split_symbols(symbol_def)

    # Check for errors.
    _check_for_errors_symbol_def(symbols)

    # Add initial delimiters.
    symbols = ["("] + symbols + [")"]

    queue: Deque = deque()
    for symbol in symbols:
        queue.append(symbol)

    return queue


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
