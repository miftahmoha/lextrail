import re
import warnings
from collections import deque
from os import getenv
from typing import Deque

from lextrail.base import Symbol, SymbolGraph, SymbolType
from lextrail.exceptions import (
    InvalidDelimiters,
    InvalidRegex,
    InvalidSymbol,
    MissingQuote,
    MissingSlash,
)
from lextrail.helpers import _is_end_def_symbol, _is_escaped
from lextrail.regex import _regex_apply_passes

_MAP_TO_STANDARD: dict[str, tuple[str, str]] = {
    "*": ("{", "}"),
    "+": ("<", ">"),
    "?": ("[", "]"),
}

_MAP_CLOSE_TO_OPEN: dict[str, str] = {")": "(", "]": "[", "}": "{", ">": "<"}


def _build_symbol_from_string(symbol_str: str) -> Symbol:
    if symbol_str.startswith('"') and symbol_str.endswith('"'):
        node = Symbol(symbol_str, SymbolType.TERMINAL)

    elif symbol_str.startswith("/") and symbol_str.endswith("/"):
        # Check if regex is valid, throw an exception otherwise.
        _check_if_valid_regex(symbol_str[1:-1])

        node = Symbol(symbol_str[1:-1], SymbolType.REGEX)

    elif symbol_str in "()[]{}<>|*?+":
        node = Symbol(symbol_str, SymbolType.SPECIAL)

    elif symbol_str.startswith("\\") and symbol_str[1:].isdigit():
        node = Symbol(symbol_str, SymbolType.REFERENCE)

    else:
        node = Symbol(symbol_str, SymbolType.NON_TERMINAL)

    return node


def _is_valid_symbol_syntax(symbol_str: str) -> bool:
    # Special characters REGEX.
    regex = re.compile(r"[@!#$%^&*()<>?/\\|}~:]")

    def _is_terminal(symbol_str: str):
        return symbol_str[0] == '"' and symbol_str[-1] == '"'

    def _is_non_terminal(symbol_str: str):
        return (
            symbol_str[0] != '"'
            and symbol_str[-1] != '"'
            and (regex.search(symbol_str) is None)
        )

    def _is_regex(symbol_str: str):
        return symbol_str.startswith("/") and symbol_str.endswith("/")

    def _is_special(symbol_str: str):
        return symbol_str in "()[]{}/<>|*+?" and len(symbol_str) == 1

    def _is_reference(symbol_str: str):
        return symbol_str.startswith("\\") and symbol_str[1:].isdigit()

    return (
        _is_terminal(symbol_str)
        or _is_non_terminal(symbol_str)
        or _is_regex(symbol_str)
        or _is_special(symbol_str)
        or _is_reference(symbol_str)
    )


# Checks if regex is valid.
def _check_if_valid_regex(pattern):
    try:
        re.compile(pattern)
        return True
    except re.error:
        raise InvalidRegex(f"The regex expression {pattern} is invalid.")


# This checks if the symbol's syntax is correct.
def _check_symbol_syntax(symbol_def_str: list[str]):
    for symbol_str in symbol_def_str:
        # 1) Check for symbol validity.
        if not _is_valid_symbol_syntax(symbol_str):
            raise InvalidSymbol(f"Invalid symbol name {symbol_str}.")


# Throws exception if delimiters are invalid.
# [TODO] Need to update delimiters for messages.
def _check_for_delimiter_coherence(symbol_def_str: list[str]):
    stack_delim_tracker: Deque[tuple[int, str]] = deque()

    # We capture the index to send useful error messages.
    for symbol_index, symbol_str in enumerate(symbol_def_str):
        if symbol_str in "([{<":
            stack_delim_tracker.append((symbol_index, symbol_str))

        elif symbol_str in ")]}>":
            in_delim = _MAP_CLOSE_TO_OPEN[symbol_str]
            if not stack_delim_tracker or stack_delim_tracker[-1][1] != in_delim:
                raise InvalidDelimiters(
                    f'No opening delimiter `{in_delim}` found for `{symbol_str}` in `{" ".join(symbol_def_str[:symbol_index])} <<{symbol_def_str[symbol_index]}>>`.'
                )
            stack_delim_tracker.pop()

    # Raise an exception if the stack is not empty.
    if stack_delim_tracker:
        symbol_index, symbol_str = stack_delim_tracker[-1]
        raise InvalidDelimiters(
            f'Non enclosed delimiter `{symbol_str}` in `{" ".join(symbol_def_str[:symbol_index+1])}`.'
        )


# This checks if the definition is correct.
def _check_for_errors_symbol_def(symbol_def_str: list[str]):
    _check_symbol_syntax(symbol_def_str)
    _check_for_delimiter_coherence(symbol_def_str)


def _split_symbols(symbol_def_str: str) -> list[str]:
    in_quote = False
    in_regex = False
    is_escaped_quote = False
    result: list[str] = []
    current: list[str] = []
    i = 0

    while i < len(symbol_def_str):
        current_character = symbol_def_str[i]

        # Dealing with regex expressions.
        if current_character == "/" and not in_regex and not in_quote:
            warnings.warn(
                "Ensure that `/` is always escaped inside the regex expression `/`-> `\\/` to avoid an undefined behavior",
            )

            if current:
                result.append("".join(current))
                current.clear()
            current.append(current_character)
            in_regex = not in_regex

        elif (
            current_character == "/"
            and in_regex
            and not in_quote
            and not _is_escaped(symbol_def_str, i - 1)
        ):
            result.append("".join(current) + current_character)
            current.clear()
            in_regex = not in_regex

        # Dealing with an escaped quote "\\"".
        # `"` is used as symbol delimiters for terminals (`"<symbol_name>"`), but for the user to express `"`
        # as a terminal, he/she needs to escape it as follows "\\"".
        elif (
            current_character == "\\"
            and not _is_escaped(symbol_def_str, i - 1)
            and symbol_def_str[i + 1] == '"'
            and in_quote
        ):
            is_escaped_quote = not is_escaped_quote

        # Dealing with `|`.
        elif current_character == "|" and not in_quote and not in_regex:
            if current:
                result.append("".join(current))
                current.clear()
            result.append(current_character)
            i += 1
            continue

        # Converting ()*, ()+ and ()? syntax to standard.
        # [TODO] We'll remove standard syntax gradually.
        elif (
            current_character == ")"
            and i + 1 < len(symbol_def_str)
            and symbol_def_str[i + 1] in "+*?"
            and not in_quote
            and not in_regex
        ):
            if current:
                result.append("".join(current))
                current.clear()
            # Convert `*+?` to standard `)]}`.
            result.append(_MAP_TO_STANDARD[symbol_def_str[i + 1]][1])
            # Convert `*+?` to standard `([{`.
            stack_idx = 0
            for idx in reversed(range(len(result))):
                if result[idx] == "(":
                    if stack_idx != 0:
                        stack_idx -= 1
                    else:
                        result[idx] = _MAP_TO_STANDARD[symbol_def_str[i + 1]][0]
                        break
                elif result[idx] == ")":
                    stack_idx += 1
            # Jump over `*+?`.
            i += 2
            continue

        # Converting <symbol><quantifier> to (<symbol>)<quantifier>.
        # [TODO] Needs a test.
        elif (
            current_character in "*+?"
            and symbol_def_str[i - 1] != ")"
            and not (in_regex or in_quote)
        ):
            symbol = "".join(current) if current else result.pop()
            result.extend(
                [
                    _MAP_TO_STANDARD[current_character][0],
                    symbol,
                    _MAP_TO_STANDARD[current_character][1],
                ]
            )
            current.clear()

        # Dealing with special delimiters.
        elif current_character in "()[]{}<>" and not in_quote and not in_regex:
            # Separating delimiters from non-terminal symbols.
            if current:
                result.append("".join(current))
                current.clear()
            result.append(current_character)

        # Dealing with quotes.
        elif current_character == '"':
            if in_regex:
                current.append('"')

            elif is_escaped_quote:
                current.append('"')
                is_escaped_quote = not is_escaped_quote

            elif in_quote:
                current.append('"')
                result.append("".join(current))
                current.clear()
                in_quote = not in_quote

            else:
                if current:
                    result.append("".join(current))
                    current.clear()
                current.append(current_character)
                in_quote = not in_quote

        # Dealing with spaces.
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

    if in_regex:
        raise MissingSlash(
            "Slash `/` is missing, regex should be expressed as /<regex_content>/."
        )

    return result


def _parse_regex(symbols: list[str]):
    result: list[str] = []
    i = 0

    while i < len(symbols):
        current_symbol = symbols[i]

        if current_symbol.startswith("/") and current_symbol.endswith("/"):
            result.extend(_regex_apply_passes(current_symbol[1:-1]))

        else:
            result.append(current_symbol)

        i += 1

    return result


def _adjust_regex_backreferences(symbols: list[str]):
    backref_details: list[tuple[int, int, int, int]] = []
    bracket_count = 0

    for i, item in enumerate(symbols):
        # Count opening brackets before finding regex patterns.
        if item in ["(", "[", "{", "<"]:
            bracket_count += 1
            continue

        if item.startswith("/") and item.endswith("/"):
            # Remove the enclosing slashes to get the regex pattern.
            pattern = item[1:-1]

            # Find positions of backreferences.
            j = 0
            while j < len(pattern):
                # Look for a backslash.
                if pattern[j] == "\\":
                    # If it's not escaped (not preceeded by another backslash).
                    if not _is_escaped(pattern, j - 1):
                        # Check if next char is a digit.
                        start_pos = j
                        j += 1
                        # Collect all consecutive digits to get the full backreference.
                        while j < len(pattern) and pattern[j].isdigit():
                            j += 1
                        # Only add if we found at least one digit. Probably useless CF.
                        if j > start_pos + 1:
                            backref_details.append((i, start_pos + 1, j, bracket_count))
                            continue
                j += 1

    for order, start, end, offset in backref_details:
        current_symbol = symbols[order]
        # Add the offset since backreference are applied not only to REGEX, but the whole expression containing both TERMINAL and REGEX symbols.
        reference = int(current_symbol[start + 1 : end + 1]) + offset
        symbols[order] = (
            current_symbol[: start + 1] + f"{reference+1}" + symbols[order][end + 1 :]
        )


def _split_terminals_into_chars(symbols: list[str]) -> list[str]:
    result: list[str] = []
    i = 0

    while i < len(symbols):
        current_symbol = symbols[i]

        if current_symbol.startswith('"') and current_symbol.endswith('"'):
            result.extend([f'"{symbol}"' for symbol in list(current_symbol[1:-1])])

        else:
            result.append(current_symbol)

        i += 1

    return result


def _convert_str_def_to_str_queue(symbol_def: str) -> Deque[str]:
    symbols = _split_symbols(symbol_def)

    # Add the offset since backreference are applied not only to REGEX, but the whole expression containing both TERMINAL and REGEX symbols.
    _adjust_regex_backreferences(symbols)

    if int(getenv("PARSE_REGEX", 1)):
        symbols = _parse_regex(symbols)

    if int(getenv("SPLIT_CHARS", 1)):
        symbols = _split_terminals_into_chars(symbols)

    # Check for errors.
    _check_for_errors_symbol_def(symbols)

    # Add initial delimiters.
    symbols = ["("] + symbols + [")"]

    queue: Deque = deque()
    for symbol in symbols:
        queue.append(symbol)

    return queue


"""
    Skipping rule.
"""


def _get_once_initial_end_def_symbols(symbol_graph: SymbolGraph):
    once_end_def_symbols_in_tree: list[Symbol] = []
    once_end_def_symbols_in_initials: list[Symbol] = []

    for symbol_initial in symbol_graph.initials:
        if _is_end_def_symbol(symbol_initial):
            once_end_def_symbols_in_initials.append(symbol_initial)

    for symbol_successors in symbol_graph.tree.values():
        for symbol_successor in symbol_successors:
            if _is_end_def_symbol(
                symbol_successor
            ) and symbol_successor not in once_end_def_symbols_in_tree + list(
                symbol_graph.finals
            ):
                once_end_def_symbols_in_tree.append(symbol_successor)

    return once_end_def_symbols_in_tree, once_end_def_symbols_in_initials
