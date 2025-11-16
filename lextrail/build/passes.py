import os
from collections import deque
from typing import Deque

from lextrail.base import Symbol, Symbol_Kind
from lextrail.exceptions import SyntaxError
from lextrail.regex import re_parse


def build_symbol_from_lexeme(content: str) -> Symbol:
    if content.startswith('"') and content.endswith('"'):
        node = Symbol(content[1:-1], Symbol_Kind.TERMINAL)

    elif content.startswith("/") and content.endswith("/"):
        node = Symbol(content[1:-1], Symbol_Kind.REGEX)

    elif content.startswith("$<") and content.endswith(">"):
        node = Symbol(content[2:-1], Symbol_Kind.REFERENCE)

    else:
        node = Symbol(content, Symbol_Kind.VARIABLE)

    return node


def _is_valid_lexeme_syntax(lexeme: str) -> bool:
    def _is_invalid_word(lexeme: str):
        return any(c in lexeme for c in "@!#$%^&*()[]{}<>?/\\|~:")

    def _is_terminal(lexeme: str):
        return lexeme.startswith('"') and lexeme.endswith('"')

    def _is_variable(lexeme: str):
        return not (
            lexeme.startswith('"') or lexeme.endswith('"') or _is_invalid_word(lexeme)
        )

    def _is_regex(lexeme: str):
        return lexeme.startswith("/") and lexeme.endswith("/")

    def _is_special(lexeme: str):
        return len(lexeme) == 1 and lexeme in "()[]{}/|*+?"

    def _is_reference(symbol_str: str):
        return (
            symbol_str.startswith("?<") or symbol_str.startswith("$<")
        ) and symbol_str.endswith(">")

    return (
        _is_terminal(lexeme)
        or _is_variable(lexeme)
        or _is_regex(lexeme)
        or _is_special(lexeme)
        or _is_reference(lexeme)
    )


def _check_lexeme_syntax(lexemes: list[str]) -> None:
    for lexeme in lexemes:
        if not _is_valid_lexeme_syntax(lexeme):
            raise SyntaxError(f"Invalid lexeme `{lexeme}`.")


def _check_lexeme_delimiters(lexemes: list[str]) -> None:
    CLOSING_TO_OPENING: dict[str, str] = {")": "(", "]": "[", "}": "{"}
    delimiter_stack: Deque[tuple[int, str]] = deque()

    for index, lexeme in enumerate(lexemes):
        if lexeme in "([{":
            delimiter_stack.append((index, lexeme))

        elif lexeme in ")]}":
            expected_opening = CLOSING_TO_OPENING[lexeme]

            if not delimiter_stack or delimiter_stack[-1][1] != expected_opening:
                context = " ".join(lexemes[:index])
                raise SyntaxError(
                    f"No opening delimiter `{expected_opening}` found for `{lexeme}` "
                    f"in `{context} <<{lexeme}>>`."
                )

            delimiter_stack.pop()

    if delimiter_stack:
        index, lexeme = delimiter_stack[-1]
        context = " ".join(lexemes[: index + 1])
        raise SyntaxError(f"Unclosed delimiter `{lexeme}` in `{context}`.")


def _check_lexeme_errors(lexemes: list[str]) -> None:
    _check_lexeme_syntax(lexemes)
    _check_lexeme_delimiters(lexemes)


def split_definition_into_lexemes(definition: str) -> list[str]:
    DELIMITERS = set("()[]{}|")
    QUANTIFIERS = {
        "?": (["["], ["]"]),
        "+": (["{"], ["}"]),
        "*": (["{", "["], ["]", "}"]),
    }

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
        return definition[i + offset] if -1 < i + offset < len(definition) else None

    while i < len(definition):
        char = definition[i]

        # === REGEX ===
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

        # === QUOTE ===
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

        # === QUANTIFIER ===
        elif char in QUANTIFIERS and not in_quote and not in_regex:
            prevc = peek(-1)
            if prevc == ")":
                open_br, close_br = QUANTIFIERS[char]

                assembled, depth = [], -1
                while (last := lexemes.pop()) != "(" or depth != 0:
                    assembled.append(last)
                    depth += 1 if last == ")" else -1 if last == "(" else 0

                assembled.append(last)

                lexemes += open_br + assembled[::-1] + close_br
            elif prevc == "(":
                lexeme.append(char)
            elif prevc == "":
                lexemes.append(char)
            else:
                # Wrap previous symbol in brackets.
                symbol = (
                    "".join(lexeme) if lexeme else lexemes.pop()
                )  # Accumulated, not yet consumed lexeme, or consumed `/.../` or `"..."`.
                lexeme.clear()
                open_br, close_br = QUANTIFIERS[char]
                lexemes += open_br + [symbol] + close_br

        # === DELIMITERS ===
        elif char in DELIMITERS and not in_quote and not in_regex:
            consume_lexeme()
            lexemes.append(char)

        # === REFERENCES ===
        elif char == "<" and not in_quote and not in_regex:
            if peek(-1) == "$" or (peek(-1) == "?" and peek(-2) == "("):
                k = 0
                while (nextc := peek(k)) != ">":
                    lexeme.append(nextc)
                    k += 1

                lexeme.append(nextc)
                consume_lexeme()
                i += k + 1
                continue
            else:
                lexeme.append(char)

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
        raise SyntaxError(
            'Unclosed quote: terminals must be expressed as "<terminal>".'
        )

    if in_regex:
        raise SyntaxError(
            "Unclosed regex: expressions must be expressed as /<pattern>/."
        )

    return lexemes


def _parse_regex(lexemes: list[str]):
    result: list[str] = []
    i = 0

    while i < len(lexemes):
        lexeme = lexemes[i]

        if lexeme.startswith("/") and lexeme.endswith("/"):
            re_output = re_parse(lexeme[1:-1])
            result += ["("] + re_output + [")"]
        else:
            result.append(lexeme)

        i += 1

    return result


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

    if int(os.getenv("PARSE_REGEX", 1)):
        lexemes = _parse_regex(lexemes)

    if int(os.getenv("SPLIT_CHARS", 0)):
        lexemes = _split_terminals_into_chars(lexemes)

    _check_lexeme_errors(lexemes)

    queue: Deque = deque()
    for lexeme in ["("] + lexemes + [")"]:
        queue.append(lexeme)

    return queue
