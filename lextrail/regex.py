from dataclasses import dataclass
from enum import Enum
import os
import string

from lextrail.helpers import TrailError, consume_lexeme, peek, is_escaped, format_error


class MarkerKind(Enum):
    EMPTY = 0
    GROUP = 1
    INTERVAL = 2
    CLASS = 3


@dataclass
class SplitMarker:
    index: int = 0
    kind: MarkerKind = MarkerKind.EMPTY


def re_split(regex: str) -> list[str]:
    lexemes: list[str] = []
    is_char_class = False
    is_intv_quant = False
    accumulate: list[str] = []
    markers: list[SplitMarker] = []
    i = 0

    def accumulate_reference(accumulate: list[str], prefix: str):
        assert prefix in "?$", "Invalid reference prefix."

        k = 0

        accumulate.extend([prefix, peek(regex, i, 1)])
        k += 2

        while (curr := peek(regex, i, k)) != ">":
            if curr.isalnum() or curr == "_":
                accumulate.append(curr)
            else:
                raise TrailError(
                    format_error(
                        "Reference name must be a word.",
                        regex[:i],
                        regex[i : i + k + 1],
                    )
                )
            k += 1

        accumulate.append(curr)

    while i < len(regex):
        curr = regex[i]

        if curr == "[":
            if is_escaped(regex, i):
                accumulate.append(curr)
            elif is_char_class:
                accumulate.append(f"\\{curr}")
            else:
                next = peek(regex, i, 1)

                if next == "]":
                    accumulate.append(str())
                else:
                    consume_lexeme(lexemes, accumulate)
                    lexemes.append(curr)

                    markers.append(SplitMarker(index=i, kind=MarkerKind.CLASS))
                    is_char_class = True

        elif curr == "]":
            if is_escaped(regex, i):
                accumulate.append(curr)
            else:
                if is_char_class:
                    consume_lexeme(lexemes, accumulate)
                    lexemes.append(curr)

                    kind = markers[-1].kind if markers else None
                    assert (
                        kind == MarkerKind.CLASS
                    ), f"Expected a `MarkerKind.CLASS` marker, found `{kind}`."

                    markers.pop()
                    is_char_class = False
                else:
                    raise TrailError(
                        format_error("Unmatched closing bracket `]`.", regex[:i], "]")
                    )

        elif curr == "{":
            if is_escaped(regex, i):
                accumulate.append(curr)
            elif is_char_class:
                accumulate.append(f"\\{curr}")
            else:
                prev, next = peek(regex, i, -1), peek(regex, i, 1)

                if prev in "*+?}(":
                    raise TrailError(
                        format_error(
                            "Invalid quantifier precedence.",
                            regex[: i - 1],
                            f"{prev}{{",
                        )
                    )
                elif prev == str():
                    raise TrailError(
                        format_error(
                            "Interval quantifiers must be precedented by either an expression or a group.",
                            str(),
                            regex[:i],
                        )
                    )
                elif next == "}":
                    raise TrailError(
                        format_error("Invalid interval quantifier.", regex[:i], "{}")
                    )
                else:
                    consume_lexeme(lexemes, accumulate)
                    lexemes.append(curr)

                    markers.append(SplitMarker(index=i, kind=MarkerKind.INTERVAL))
                    is_intv_quant = True

        elif curr == "}":
            if is_escaped(regex, i):
                accumulate.append(curr)
            elif is_char_class:
                accumulate.append(f"\\{curr}")
            else:
                next = peek(regex, i, 1)

                if is_intv_quant:
                    consume_lexeme(lexemes, accumulate)

                    assert (
                        len(lexemes) >= 2
                    ), "`is_intv_quant` ensures the existence of `{` and `{}` raises an error early."

                    bracket, quantifier = lexemes[-2], lexemes[-1]
                    parts = [part.strip() for part in quantifier.split(",")]

                    if (
                        bracket == "{"
                        and len(parts) <= 2
                        and all(part == "" or part.isdigit() for part in parts)
                    ):
                        if (
                            len(parts) == 2
                            and all(part.isdigit() for part in parts)
                            and int(parts[1]) < int(parts[0])
                        ):
                            raise TrailError(
                                format_error(
                                    "Interval quantifier bounds out of order.",
                                    regex[: i - len(quantifier) - 1],
                                    f"{{{quantifier}}}",
                                )
                            )

                        lexemes.append(curr)
                    else:
                        raise TrailError(
                            format_error(
                                "Invalid interval quantifier.",
                                regex[: i - len(quantifier) - len(bracket)],
                                f"{bracket}{quantifier}}}",
                            )
                        )

                    kind = markers[-1].kind if markers else None
                    assert (
                        kind == MarkerKind.INTERVAL
                    ), f"Expected a `MarkerKind.INTERVAL` marker, found `{kind}`."

                    markers.pop()
                    is_intv_quant = False
                else:
                    raise TrailError(
                        format_error("Unmatched closing bracket `}`.", regex[:i], "}")
                    )

        elif curr == "(":
            if is_escaped(regex, i):
                accumulate.append(curr)
            elif is_char_class:
                accumulate.append(f"\\{curr}")
            else:
                consume_lexeme(lexemes, accumulate)
                lexemes.append(curr)

                markers.append(SplitMarker(index=i, kind=MarkerKind.GROUP))

        elif curr == ")":
            if is_escaped(regex, i):
                accumulate.append(curr)
            elif is_char_class:
                accumulate.append(f"\\{curr}")
            elif markers:
                consume_lexeme(lexemes, accumulate)
                lexemes.append(curr)

                kind = markers[-1].kind if markers else None
                assert (
                    kind == MarkerKind.GROUP
                ), f"Expected a `MarkerKind.GROUP` marker, found `{kind}`."

                markers.pop()
            else:
                raise TrailError(
                    format_error("Unmatched closing bracket `)`.", regex[:i], ")")
                )

        # === BACKREFERENCES ===
        elif curr.isdigit():
            if is_escaped(regex, i):
                raise TrailError(
                    format_error(
                        "Unsupported backreference format, use `(?<alphanumeric>...)` to capture, and `$<alphanumeric>` to load instead.",
                        regex[: i - 1],
                        f"\\{curr}",
                    )
                )
            else:
                accumulate.append(curr)

        elif curr == "?":
            if is_escaped(regex, i):
                accumulate.append(curr)
            elif is_char_class:
                accumulate.append(f"\\{curr}")
            else:
                prev, next = peek(regex, i, -1), peek(regex, i, 1)

                if prev == str():
                    raise TrailError(
                        format_error(
                            "Quantifiers must be precedented by either an expression or a group.",
                            str(),
                            curr,
                        )
                    )
                elif prev in "*+?}":
                    raise TrailError(
                        format_error(
                            "Invalid quantifier precedence.", regex[: i - 1], f"{prev}?"
                        )
                    )
                elif prev == "(" and not is_escaped(regex, i - 1):
                    skip = peek(regex, i, 2)

                    if next == "<" and skip not in "=!":
                        assert not accumulate, "`accumulate` expected to be empty."

                        accumulate_reference(accumulate, curr)
                        i += len(accumulate)

                        consume_lexeme(lexemes, accumulate)
                        continue
                    else:
                        raise TrailError(
                            format_error(
                                "Unsupported question-mark construct.",
                                regex[: i - 1],
                                f"(?{next}{skip}",
                            )
                        )
                else:
                    consume_lexeme(lexemes, accumulate)
                    lexemes.append(curr)

        elif curr == "$":
            if is_escaped(regex, i):
                accumulate.append(curr)
            elif is_char_class:
                accumulate.append(f"\\{curr}")
            else:
                next = peek(regex, i, 1)

                if next == "<":
                    consume_lexeme(lexemes, accumulate)

                    accumulate_reference(accumulate, curr)
                    i += len(accumulate)

                    consume_lexeme(lexemes, accumulate)
                    continue
                elif next == "|" or next == str():
                    pass
                else:
                    raise TrailError(
                        format_error(
                            "Misplaced anchor, escape with `\\` for literal dollar sign.",
                            regex[:i],
                            "$",
                        )
                    )

        elif curr == "^":
            if is_escaped(regex, i):
                accumulate.append(curr)
            else:
                prev, next = peek(regex, i, -1), peek(regex, i, 1)

                if is_char_class:
                    if prev == "[" and not is_escaped(regex, i - 1):
                        if next == "]":
                            lexemes.append(str())
                        else:
                            assert not accumulate, "`accumulate` expected to be empty."

                            lexemes.append(curr)
                    else:
                        accumulate.append(f"\\{curr}")
                else:
                    if prev == "|" or prev == str():
                        pass
                    else:
                        raise TrailError(
                            format_error(
                                "Misplaced anchor, escape with `\\` for literal dollar sign.",
                                regex[:i],
                                "^",
                            )
                        )

        elif curr == "-":
            if is_escaped(regex, i):
                accumulate.append(curr)
            else:
                if is_char_class:
                    prev, next = peek(regex, i, -1), peek(regex, i, 1)

                    if next == "]":
                        accumulate.append(f"\\{curr}")
                    else:
                        if accumulate:
                            if prev.isalnum() and next.isalnum():
                                start, end = ord(prev), ord(next)

                                if start <= end:
                                    accumulate.pop()
                                    consume_lexeme(lexemes, accumulate)

                                    lexemes.extend([prev, curr, next])
                                    i += 1
                                else:
                                    raise TrailError(
                                        format_error(
                                            f"Character range '{start}-{end}' is invalid: start must be less than or equal to end.",
                                            regex[: i - 1],
                                            f"{prev}-{next}",
                                        )
                                    )
                            else:
                                raise TrailError(
                                    format_error(
                                        "Range contains non-alphanumeric characters.",
                                        regex[: i - 1],
                                        f"{prev}-{next}",
                                    )
                                )
                        else:
                            accumulate.append(f"\\{curr}")
                else:
                    accumulate.append(f"\\{curr}")

        elif curr == "|":
            if is_escaped(regex, i):
                accumulate.append(curr)
            elif is_char_class:
                accumulate.append(f"\\{curr}")
            else:
                consume_lexeme(lexemes, accumulate)
                lexemes.append(curr)

        elif curr == ".":
            if is_escaped(regex, i):
                accumulate.append(curr)
            elif is_char_class:
                accumulate.append(f"\\{curr}")
            else:
                consume_lexeme(lexemes, accumulate)
                lexemes.append(curr)

        # === QUANTIFIERS ===
        # [NOTE] `?` is handled separately, since it could also act as a reference in `?<...>`.
        elif curr in "+*":
            if is_escaped(regex, i):
                accumulate.append(curr)
            elif is_char_class:
                accumulate.append(f"\\{curr}")
            else:
                prev = peek(regex, i, -1)

                if prev == str():
                    raise TrailError(
                        format_error(
                            "Quantifiers must be precedented by either an expression or a group.",
                            str(),
                            curr,
                        )
                    )
                elif prev in "*+?}(":
                    raise TrailError(
                        format_error(
                            "Invalid quantifier precedence.",
                            regex[: i - 1],
                            f"{prev}{curr}",
                        )
                    )
                else:
                    consume_lexeme(lexemes, accumulate)
                    lexemes.append(curr)

        # === PREDEFINED CHARACTER CLASSES ===
        # Supported.
        elif curr in "dDwWsS":
            if is_escaped(regex, i):
                accumulate.pop()
                consume_lexeme(lexemes, accumulate)
                lexemes.append(f"\\{curr}")
            else:
                accumulate.append(curr)

        # Unsupported.
        elif curr in "bB":
            if is_escaped(regex, i):
                raise TrailError(
                    f"Predefined escape character \\{curr} is not supported."
                )
            else:
                accumulate.append(curr)

        # === BACKSLASH ===
        # (1) If the character that comes after has no QUIRKS, then the escape will be ignored.
        # (2) Since escapes should be escaped if they're expected to be LITERAL with "\\\\" or r'\\',
        # then the escape will be ignored too.
        elif curr == "\\":
            if is_escaped(regex, i):
                accumulate.append(curr)
            else:
                next = peek(regex, i, 1)

                if next in ESCAPABLE:
                    accumulate.append(curr)
                elif next.isdigit() or next == "/":
                    pass
                else:
                    raise TrailError(
                        format_error(
                            "Invalid escape character.", regex[:i], f"\\{next}"
                        )
                    )

        else:
            accumulate.append(curr)

        i += 1

    consume_lexeme(lexemes, accumulate)

    marker = markers.pop() if markers else SplitMarker()

    match marker.kind:
        case MarkerKind.GROUP:
            raise TrailError(
                format_error(
                    "Unmatched '(' - expected a closing ')'.",
                    regex[: marker.index],
                    "(",
                )
            )
        case MarkerKind.CLASS:
            raise TrailError(
                format_error(
                    "Unmatched '[' - expected a closing ']'.",
                    regex[: marker.index],
                    "[",
                )
            )
        case MarkerKind.INTERVAL:
            raise TrailError(
                format_error(
                    "Unmatched '{' - expected a closing '}'.",
                    regex[: marker.index],
                    "{",
                )
            )

    return ["("] + lexemes + [")"]


def re_expand(chunks: list[str]):
    DIGITS = expand_ascii("0", "9")
    NOT_DIGITS = chain(
        DIGITS,
        exclude_from_ascii,
        include_escapes,
    )
    WORD = DIGITS + expand_ascii("a", "z") + expand_ascii("A", "Z") + "_"
    NOT_WORD = chain(
        WORD,
        exclude_from_ascii,
        include_escapes,
    )
    SPACE = " \t\n\r\f\v"
    NOT_SPACE = chain(
        " ",
        exclude_from_ascii,
        include_escapes,
    )
    WILDCARD = chain(
        "\n",
        exclude_from_ascii,
        include_escapes,
    )

    lexemes: list[str] = []
    is_char_class = False
    is_complement = False
    i = 0

    while i < len(chunks):
        chunk = chunks[i]

        if chunk == "[":
            is_char_class = True
            lexemes.append(chunk)

        elif chunk == "]":
            is_char_class = False

            assembled: list[str] = []
            while (lexeme := lexemes.pop()) != "[":
                assembled.append(lexeme)

            assert assembled, "Expected non-empty character class."

            assembled = "".join(assembled[::-1])

            if is_complement:
                assembled = chain(
                    assembled,
                    exclude_escapes,
                    exclude_from_ascii,
                    include_escapes,
                )
                is_complement = False

            lexemes += ["[", assembled, "]"]

        elif chunk == "^":
            is_complement = True

        # === CHARACTER RANGE ===
        elif chunk == "-":
            low, up = lexemes.pop(), peek(chunks, i, 1)
            lexemes.append(expand_ascii(low, up))

            i += 2
            continue

        # === PREDEFINED CHARACTER CLASSES ===
        # [NOTE] PCCEs don't become literal inside brackets.
        elif chunk == "\\d":
            lexemes += [DIGITS] if is_char_class else ["[", DIGITS, "]"]

        elif chunk == "\\D":
            lexemes += [NOT_DIGITS] if is_char_class else ["[", NOT_DIGITS, "]"]

        elif chunk == "\\w":
            lexemes += [WORD] if is_char_class else ["[", WORD, "]"]

        elif chunk == "\\W":
            lexemes += [NOT_WORD] if is_char_class else ["[", NOT_WORD, "]"]

        elif chunk == "\\s":
            lexemes += [SPACE] if is_char_class else ["[", SPACE, "]"]

        elif chunk == "\\S":
            lexemes += [NOT_SPACE] if is_char_class else ["[", NOT_SPACE, "]"]

        # === WILDCARD ===
        elif chunk == ".":
            lexemes += ["[", WILDCARD, "]"]

        else:
            lexemes.append(chunk)

        i += 1

    return lexemes


def re_norm(chunks: list[str]):
    QUANTIFIERS = {
        "?": (["["], ["]"]),
        "+": (["{"], ["}"]),
        "*": (["{", "["], ["]", "}"]),
    }

    lexemes: list[str] = []
    i = 0

    while i < len(chunks):
        chunk = chunks[i]

        # === CHARACTER CLASSES ===
        if chunk == "[":
            next, skip = peek(chunks, i, 1), peek(chunks, i, 2)

            assert skip == "]", "Expected assembled character class."

            if int(os.getenv("TEST_MODE", 0)):
                lexemes += [
                    "(",
                    "|".join(f'"{character}"' for character in exclude_escapes(next)),
                    ")",
                ]
            else:
                lexemes += (
                    ["("]
                    + [
                        union
                        for character in exclude_escapes(next)
                        for union in (f'"{character}"', "|")
                    ][:-1]
                    + [")"]
                )

            i += 3
            continue

        # === QUANTIFIERS ===
        elif chunk in "*+?":
            assert (
                lexemes
            ), "Quantifiers must be precendented by either a expression or a group."

            open_br, close_br = QUANTIFIERS[chunk]
            prev = lexemes.pop()

            if prev == ")":
                assembled = []
                depth = 0

                while ((chunk := lexemes.pop()) != "(") or depth != 0:
                    assembled.append(chunk)
                    depth += 1 if chunk == ")" else -1 if chunk == "(" else 0

                lexemes += open_br + assembled[::-1] + close_br
            else:
                assert (
                    prev.startswith('"') and prev.endswith('"') and len(prev) == 3
                ), "Quantifier was not preceded by a terminal character."

                lexemes += open_br + [prev] + close_br

        # === INTERVAL QUANTIFIERS ===
        elif chunk == "{":
            assert (
                lexemes
            ), "Interval quantifiers must be precendented by either a expression or a group."

            prev, next = lexemes.pop(), peek(chunks, i, 1).split(",")

            # [CHECK] Interval quantifier could either be `{x, y}`, `{x,}`, `{,y}` or `{x}`.
            assert len(next) <= 2, "Interval quantifier has invalid arguments."

            args = (next[0], next[1]) if len(next) == 2 else (next[0], next[0])

            req, max = (int(args[0]) if args[0] else 0), (
                int(args[1]) if args[1] else 0
            )
            opt = max - req

            if prev == ")":
                assembled = []
                depth = 0

                while (chunk := lexemes.pop()) != "(" or depth != 0:
                    assembled.append(chunk)
                    depth += 1 if chunk == ")" else -1 if chunk == "(" else 0

                assembled.reverse()

                lexemes += (["("] + assembled + [")"]) * req + (
                    (["["] + assembled + ["]"]) * opt
                    if opt >= 0
                    else ["{", "["] + assembled + ["]", "}"]
                )
            else:
                assert (
                    prev.startswith('"') and prev.endswith('"') and len(prev) == 3
                ), "Interval quantifier was not preceded by a terminal character."

                lexemes += (
                    [prev] * req + ["[", prev, "]"] * opt
                    if opt >= 0
                    else [prev] * req + ["{", "[", prev, "]", "}"]
                )

            i += 3
            continue

        else:
            # [CHECK] The control flow ordering in the current pass will make it
            # such that `[]`, `{}` and `+*?` will be dealt with and converted.
            # Other symbols such as `.-^$` should not appear in this pass.
            assert chunk not in "[]{}.-^$+*?", "Invalid symbols at normalization pass."

            if chunk in ["(", ")", "|"] or is_named_reference(chunk):
                lexemes.append(chunk)
            else:
                curr, next = exclude_escapes(chunk), peek(chunks, i, 1)

                if next in "{*?+":
                    lexemes += [f'"{curr[:-1]}"'] + [f'"{curr[-1]}"']
                else:
                    lexemes.append(f'"{curr}"')

        i += 1

    return lexemes


def re_parse(lexeme: str):
    return chain(lexeme, re_split, re_expand, re_norm)


# ============================ HELPERS ============================
ESCAPABLE = [
    "(",
    ")",
    "[",
    "]",
    "{",
    "}",
    "d",
    "D",
    "w",
    "W",
    "s",
    "S",
    "|",
    "+",
    "*",
    "?",
    "-",
    "^",
    "$",
    ".",
]


def chain(x, *funcs):
    result = x
    for func in funcs:
        result = func(result)
    return result


def expand_ascii(start: str, end: str) -> str:
    return "".join(chr(c) for c in range(ord(start), ord(end) + 1))


CONTEXT = "()[]{}|.*?+-"


def include_escapes(exp: str) -> str:
    result: list[str] = []

    for char in exp:
        if char in CONTEXT:
            result.append("\\")

        result.append(char)

    return "".join(result)


def exclude_from_ascii(exp: str) -> str:
    return "".join([elem for elem in string.printable if elem not in exp])


def exclude_escapes(exp: str) -> str:
    result: list[str] = []

    for char in exp:
        if char in CONTEXT:
            result.pop()

        result.append(char)

    return "".join(result)


def is_named_reference(exp: str) -> bool:
    return (exp.startswith("?<") or exp.startswith("$<")) and exp.endswith(">")
