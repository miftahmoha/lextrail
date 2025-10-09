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


# [TODO] Make an symbol with an empty content not possible, it gets ignored.
# Empty NON-TERMINALs shouldn't be able to be possible, the issue would be with TERMINALs and REGEX ("" and //).
def build_symbol_from_lexeme(content: str) -> Symbol:
    if content.startswith('"') and content.endswith('"'):
        node = Symbol(content[1:-1], SymbolType.TERMINAL)

    elif content.startswith("/") and content.endswith("/"):
        # Throw an exception if regex is not valid.
        # [TODO] Is there some syntax that "I" consider as VALID that Python engine considers an ERROR?
        _is_valid_regex(content[1:-1])

        node = Symbol(content[1:-1], SymbolType.REGEX)

    elif content in "()[]{}<>|*?+":
        node = Symbol(content, SymbolType.SPECIAL)

    elif content.startswith("\\") and content[1:].isdigit():
        # [NOTE] Avoids storing results if there are no backreferences. It is
        # executed after parsing regex expressions.
        # [NOTE] Setting the environement variable doesn't seem good, also there
        # seems to be no need to put the '\\' inside the content.
        os.environ["PARSE_BREFS"] = "1"
        node = Symbol(content, SymbolType.REFERENCE)

    else:
        node = Symbol(content, SymbolType.NON_TERMINAL)

    return node


# Is there a utility for the check?
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
    DELIMITERS = set("()[]{}<>|")
    QUANTIFIERS = {"*": ("{", "}"), "+": ("<", ">"), "?": ("[", "]")}

    lexemes: list[str] = []
    in_quote = False
    in_regex = False
    lexeme: list[str] = []
    i = 0

    def consume_lexeme():
        if lexeme:
            lexemes.append("".join(lexeme))
            lexeme.clear()

    def is_escaped(pos):
        count = 0
        pos -= 1
        while pos >= 0 and definition[pos] == "\\":
            count += 1
            pos -= 1
        return count % 2 == 1

    def peek(offset):
        return definition[i + offset] if 0 < i + offset < len(definition) else None

    while i < len(definition):
        char = definition[i]

        # === REGEX HANDLING ===
        if char == "/" and not in_quote:
            if not in_regex:
                # Start regex.
                consume_lexeme()
                lexeme.append(char)
                in_regex = True
            elif not is_escaped(i):
                # End regex.
                lexeme.append(char)
                consume_lexeme()
                in_regex = False

        # === PIPE (OR) OPERATOR ===
        elif char == "|" and not in_quote and not in_regex:
            consume_lexeme()
            lexemes.append(char)

        # === QUOTE HANDLING ===
        elif char == '"' and not in_regex:
            if not in_quote:
                # Starting quote.
                consume_lexeme()
                lexeme.append(char)
                in_quote = True
            elif is_escaped(i):
                # Escaped quote inside string.
                lexeme.append(char)
            else:
                # Ending quote.
                lexeme.append(char)
                consume_lexeme()
                in_quote = False

        # === QUANTIFIER CONVERSION: ()* -> [...]  ===
        elif (
            char == ")"
            and (next_char := peek(1)) in QUANTIFIERS
            and not in_quote
            and not in_regex
        ):
            consume_lexeme()
            open_br, close_br = QUANTIFIERS[next_char]
            lexemes.append(close_br)

            # Find matching opening parenthesis and convert it.
            depth = 0
            for idx in reversed(range(len(lexemes))):
                if lexemes[idx] == ")":
                    depth += 1
                elif lexemes[idx] == "(":
                    if depth == 0:
                        lexemes[idx] = open_br
                        break
                    depth -= 1

            i += 1  # Skip the quantifier.

        # === STANDALONE QUANTIFIER: symbol* -> [symbol] ===
        elif char in QUANTIFIERS and not in_quote and not in_regex:
            if peek(-1) != ")":
                # Wrap previous symbol in brackets.
                symbol = (
                    "".join(lexeme) if lexeme else lexemes.pop()
                )  # Accumulated, not yet consumed lexeme, or consumed `/.../` or `"..."`.
                lexeme.clear()

                open_br, close_br = QUANTIFIERS[char]
                lexemes.extend([open_br, symbol, close_br])
            else:
                # `*, +, ?` as first elements.
                pass

        # === DELIMITERS ===
        elif char in DELIMITERS and not in_quote and not in_regex:
            consume_lexeme()
            lexemes.append(char)

        # === WHITESPACE ===
        elif char.isspace():
            if in_quote or in_regex:
                lexeme.append(char)
            else:
                consume_lexeme()

        # === REGULAR CHARACTERS ===
        else:
            lexeme.append(char)

        i += 1

    consume_lexeme()

    if in_quote:
        raise MissingQuote(
            'Unclosed quote: terminals must be expressed as "<terminal>".'
        )

    if in_regex:
        raise MissingSlash(
            "Unclosed regex: expressions must be expressed as /<pattern>/."
        )

    return lexemes


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


def adjust_regex_backreferences(lexemes: list[str]) -> None:
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
        adjust_regex_backreferences(lexemes)

    if int(os.getenv("PARSE_REGEX", 1)):
        lexemes = _parse_regex(lexemes)

    if int(os.getenv("SPLIT_CHARS", 1)):
        lexemes = _split_terminals_into_chars(lexemes)

    _check_lexeme_errors(lexemes)

    queue: Deque = deque()
    for lexeme in ["("] + lexemes + [")"]:
        queue.append(lexeme)

    return queue
