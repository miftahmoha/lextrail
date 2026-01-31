from dataclasses import dataclass
from enum import Enum

from lextrail.regex import re_parse
from lextrail.helpers import format_error


class TrailError(Exception):
    pass


class MarkerKind(Enum):
    EMPTY = 0
    GROUP = 1
    QUOTE = 2
    SLASH = 3


@dataclass
class SplitMarker:
    index: int = 0
    kind: MarkerKind = MarkerKind.EMPTY


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
    markers: list[SplitMarker] = []
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
        curr = definition[i]

        # === REGEX ===
        if curr == "/" and not in_quote:
            if not in_regex:
                consume_lexeme()
                lexeme.append(curr)

                markers.append(SplitMarker(index=i, kind=MarkerKind.SLASH))
                in_regex = True
            elif not is_escaped(i):
                lexeme.append(curr)

                result = re_parse(lexeme[1:-1])
                lexeme.clear()
                lexemes.extend(result)

                kind = markers[-1].kind if markers else None
                assert (
                    kind == MarkerKind.SLASH
                ), f"Expected a `MarkerKind.SLASH` marker, found `{kind}`"

                markers.pop()
                in_regex = False

        # === PIPE (OR) OPERATOR ===
        elif curr == "|" and not in_quote and not in_regex:
            consume_lexeme()
            lexemes.append(curr)

        # === QUOTE ===
        elif curr == '"' and not in_regex:
            if not in_quote:
                consume_lexeme()
                lexeme.append(curr)

                markers.append(SplitMarker(index=i, kind=MarkerKind.QUOTE))
                in_quote = True
            elif is_escaped(i):
                lexeme.append(curr)
            else:
                lexeme.append(curr)
                consume_lexeme()

                kind = markers[-1].kind if markers else None
                assert (
                    kind == MarkerKind.QUOTE
                ), f"Expected a `MarkerKind.QUOTE` marker, found `{kind}`"

                markers.pop()
                in_quote = False

        # === QUANTIFIER ===
        elif curr in QUANTIFIERS and not in_quote and not in_regex:
            prev = peek(-1)

            if prev == ")":
                open_br, close_br = QUANTIFIERS[curr]

                # [TODO] Pop could result in some runtime errors.
                assembled, depth = [], -1
                while (last := lexemes.pop()) != "(" or depth != 0:
                    assembled.append(last)
                    depth += 1 if last == ")" else -1 if last == "(" else 0

                assembled.append(last)

                lexemes += open_br + assembled[::-1] + close_br
            elif prev == "(":
                lexeme.append(curr)
            elif prev == "":
                lexemes.append(curr)
            else:
                # Wrap previous symbol in brackets.
                symbol = (
                    "".join(lexeme) if lexeme else lexemes.pop()
                )  # Accumulated, not yet consumed lexeme, or consumed `/.../` or `"..."`.
                lexeme.clear()
                open_br, close_br = QUANTIFIERS[curr]
                lexemes += open_br + [symbol] + close_br

        # === DELIMITERS ===
        elif curr in DELIMITERS and not in_quote and not in_regex:
            consume_lexeme()
            lexemes.append(curr)

            match curr:
                case "(":
                    markers.append(SplitMarker(index=i, kind=MarkerKind.GROUP))
                case ")":
                    marker = markers.pop() if markers else SplitMarker()

                    if marker.kind != MarkerKind.GROUP:
                        context = definition[:i]

                        raise TrailError(
                            format_error(
                                "Unexpected `)` - no matching opening parenthesis.",
                                context,
                                ")",
                            )
                        )
                case "|":
                    pass
                case _:
                    context = definition[:i]

                    raise TrailError(
                        format_error(
                            "This character is reserved for internal use.",
                            context,
                            curr,
                        )
                    )

        # === REFERENCES ===
        elif curr == "<" and not in_quote and not in_regex:
            if peek(-1) == "$" or (peek(-1) == "?" and peek(-2) == "("):
                k = 0
                while (next := peek(k)) != ">":
                    lexeme.append(next)
                    k += 1

                lexeme.append(next)
                consume_lexeme()
                i += k + 1
                continue
            else:
                lexeme.append(curr)

        # === WHITESPACE ===
        elif curr.isspace():
            if in_quote or in_regex:
                lexeme.append(curr)
            else:
                consume_lexeme()

        # === REGULAR CHARACTERS ===
        else:
            lexeme.append(curr)

        i += 1

    consume_lexeme()

    marker = markers.pop() if markers else SplitMarker()

    match marker.kind:
        case MarkerKind.SLASH:
            raise TrailError(
                format_error(
                    "Unterminated regex pattern starting with `/` - add closing delimiter or escape `/` as `\\/`.",
                    definition[: marker.index],
                    "/",
                )
            )
        case MarkerKind.GROUP:
            raise TrailError(
                format_error(
                    "Unmatched '(' - expected a closing ')'.",
                    definition[: marker.index],
                    "(",
                )
            )
        case MarkerKind.QUOTE:
            raise TrailError(
                format_error(
                    'Unclosed string literal - missing " to terminate the string.',
                    definition[: marker.index],
                    '"',
                )
            )

    return ["("] + lexemes + [")"]


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
