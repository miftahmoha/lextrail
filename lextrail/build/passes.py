import os
import re
import warnings
from collections import defaultdict, deque
from typing import Deque

from lextrail.base import Symbol, SymbolType
from lextrail.exceptions import (
    InvalidDelimiters,
    InvalidLexeme,
    InvalidRegex,
    MissingQuote,
    MissingSlash,
)
from lextrail.helpers import is_escaped
from lextrail.regex import _regex_apply_passes

_MAP_TO_STANDARD: dict[str, tuple[str, str]] = {
    "*": ("{", "}"),
    "+": ("<", ">"),
    "?": ("[", "]"),
}

_MAP_CLOSE_TO_OPEN: dict[str, str] = {")": "(", "]": "[", "}": "{", ">": "<"}


def _is_valid_regex(pattern):
    try:
        re.compile(pattern)
        return True
    except re.error:
        raise InvalidRegex(f"The regex expression {pattern} is invalid.")


def build_symbol_from_lexeme(content: str) -> Symbol:
    if content.startswith('"') and content.endswith('"'):
        node = Symbol(content, SymbolType.TERMINAL)

    elif content.startswith("/") and content.endswith("/"):
        # Throw an exception if regex is not valid.
        _is_valid_regex(content[1:-1])

        node = Symbol(content[1:-1], SymbolType.REGEX)

    elif content in "()[]{}<>|*?+":
        node = Symbol(content, SymbolType.SPECIAL)

    elif content.startswith("\\") and content[1:].isdigit():
        # [NOTE] Avoids storing results if there are no backreferences. It is
        # executed after parsing regex expressions.
        os.environ["PARSE_BREFS"] = "1"
        node = Symbol(content, SymbolType.REFERENCE)

    else:
        node = Symbol(content, SymbolType.NON_TERMINAL)

    return node


def _is_valid_lexeme_syntax(symbol_str: str) -> bool:
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


def _check_lexeme_syntax(lexemes: list[str]):
    for lexeme in lexemes:
        if not _is_valid_lexeme_syntax(lexeme):
            raise InvalidLexeme(f"Invalid lexeme `{lexeme}`.")


def _check_lexeme_delimiters(lexemes: list[str]) -> None:
    stack_delim_tracker: Deque[tuple[int, str]] = deque()

    for index, lexeme in enumerate(lexemes):
        if lexeme in "([{<":
            stack_delim_tracker.append((index, lexeme))

        elif lexeme in ")]}>":
            in_delim = _MAP_CLOSE_TO_OPEN[lexeme]
            if not stack_delim_tracker or stack_delim_tracker[-1][1] != in_delim:
                raise InvalidDelimiters(
                    f'No opening delimiter `{in_delim}` found for `{lexeme}` in `{" ".join(lexemes[:index])} <<{lexemes[index]}>>`.'
                )
            stack_delim_tracker.pop()

    if stack_delim_tracker:
        index, lexeme = stack_delim_tracker[-1]
        raise InvalidDelimiters(
            f'Non enclosed delimiter `{lexeme}` in `{" ".join(lexemes[:index + 1])}`.'
        )


def _check_lexeme_errors(lexemes: list[str]) -> None:
    _check_lexeme_syntax(lexemes)
    _check_lexeme_delimiters(lexemes)


def split_definition_into_lexemes(definition: str) -> list[str]:
    result: list[str] = []
    current: list[str] = []
    in_quote = False
    in_regex = False
    is_escaped_quote = False
    i = 0

    while i < len(definition):
        current_character = definition[i]

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
            and not is_escaped(definition, i - 1)
        ):
            result.append("".join(current) + current_character)
            current.clear()
            in_regex = not in_regex

        # Dealing with an escaped quote "\\"".
        # `"` is used as symbol delimiters for terminals (`"lexeme"`), to express `"` as a
        # terminal, escape it with backlash "\\"" or (r)"\"".
        elif (
            current_character == "\\"
            and not is_escaped(definition, i - 1)
            and definition[i + 1] == '"'
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
            and i + 1 < len(definition)
            and definition[i + 1] in "+*?"
            and not in_quote
            and not in_regex
        ):
            if current:
                result.append("".join(current))
                current.clear()
            # Convert `*+?` to standard `)]}`.
            result.append(_MAP_TO_STANDARD[definition[i + 1]][1])
            # Convert `*+?` to standard `([{`.
            stack_idx = 0
            for idx in reversed(range(len(result))):
                if result[idx] == "(":
                    if stack_idx != 0:
                        stack_idx -= 1
                    else:
                        result[idx] = _MAP_TO_STANDARD[definition[i + 1]][0]
                        break
                elif result[idx] == ")":
                    stack_idx += 1
            # Jump over `*+?`.
            i += 2
            continue

        # Converting <symbol><quantifier> to (<symbol>)<quantifier>.
        # [TODO] Not tested.
        elif (
            current_character in "*+?"
            and definition[i - 1] != ")"
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


def _parse_regex(lexemes: list[str]):
    result: list[str] = []
    i = 0

    while i < len(lexemes):
        lexeme = lexemes[i]

        if lexeme.startswith("/") and lexeme.endswith("/"):
            # [TODO] Do I add initial delimiters?
            converted = _regex_apply_passes(lexeme[1:-1])
            # Convert regex delimiters to standard.
            _adjust_regex_delimiters(converted)
            result.extend(converted)

        else:
            result.append(lexeme)

        i += 1

    return result


def _adjust_regex_delimiters(lexemes: list[str]):
    i = 0

    while i < len(lexemes):
        lexeme = lexemes[i]

        if lexeme == ")" and i + 1 < len(lexemes) and lexemes[i + 1] in "+*?":
            # Convert `*+?` to standard `)]}`.
            lexemes[i] = _MAP_TO_STANDARD[lexemes[i + 1]][1]
            # Convert `*+?` to standard `([{`.
            stack_idx = 0
            for idx in reversed(range(i)):
                if lexemes[idx] == "(":
                    if stack_idx != 0:
                        stack_idx -= 1
                    else:
                        lexemes[idx] = _MAP_TO_STANDARD[lexemes[i + 1]][0]
                        break
                elif lexemes[idx] == ")":
                    stack_idx += 1
            lexemes.pop(i + 1)

        i += 1


def _adjust_regex_backreferences(lexemes: list[str]) -> None:
    regex_references_details: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    outer_open_bracket_count, inner_open_bracket_count = 0, 0

    for i, item in enumerate(lexemes):
        if item in ["(", "[", "{", "<"]:
            outer_open_bracket_count += 1
            continue

        if item.startswith("/") and item.endswith("/"):
            outer_open_bracket_count += inner_open_bracket_count
            inner_open_bracket_count = 0

            j = 0
            while j < len(item):
                if item[j] == "(" and not is_escaped(item, j - 1):
                    inner_open_bracket_count += 1

                if (
                    item[j] == "\\"
                    and not is_escaped(item, j - 1)
                    and (j + 1) < len(item)  # Runtime bounds checking.
                    and item[j + 1].isdigit()
                ):
                    j += 1
                    start_pos = j

                    while j < len(item) and item[j].isdigit():
                        j += 1

                    regex_references_details[i].append(
                        (start_pos, j, outer_open_bracket_count)
                    )
                    continue

                j += 1

    for index, details in regex_references_details.items():
        lexeme = lexemes[index]
        shift = 0

        for start, end, offset in details:
            reference = int(lexeme[start:end]) + offset

            lexemes[index] = (
                lexemes[index][: start + shift]
                + f"{reference + 1}"  # The `+ 1` accounts of the added initial brackets.
                + lexemes[index][end + shift :]
            )

            # If a reference is replaced with a number with more digits, then
            # the index shift needs to be accounted in the next replacement.
            shift = len(str(reference + 1)) - len(lexeme[start:end])


def _split_terminals_into_chars(lexemes: list[str]) -> list[str]:
    result: list[str] = []
    i = 0

    while i < len(lexemes):
        lexeme = lexemes[i]

        if lexeme.startswith('"') and lexeme.endswith('"'):
            result.extend([f'"{character}"' for character in list(lexeme[1:-1])])

        else:
            result.append(lexeme)

        i += 1

    return result


def definition_into_lexeme_queue(definition: str) -> Deque[str]:
    lexemes = split_definition_into_lexemes(definition)

    if int(os.getenv("PARSE_BREFS", 1)):
        # Backreference is supported on the whole EBNF format, thus, we must adjust
        # the reference on the regex side.
        _adjust_regex_backreferences(lexemes)

    if int(os.getenv("PARSE_REGEX", 1)):
        lexemes = _parse_regex(lexemes)

    if int(os.getenv("SPLIT_CHARS", 1)):
        lexemes = _split_terminals_into_chars(lexemes)

    _check_lexeme_errors(lexemes)

    queue: Deque = deque()
    for lexeme in ["("] + lexemes + [")"]:
        queue.append(lexeme)

    return queue
