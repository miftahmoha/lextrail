import os
import string

from lextrail.exceptions import InvalidRegex


def re_split(regex: str) -> list[str]:
    lexemes: list[str] = []
    is_char_class: bool = False
    lexeme: list[str] = []
    i = 0

    def exp_char_set(low: str, up: str) -> str:
        return "".join(chr(c) for c in range(ord(low), ord(up) + 1))

    def consume_lexeme():
        if lexeme:
            lexemes.append("".join(lexeme))
            lexeme.clear()

    def consume_reference(prefix: str):
        WORD = (
            exp_char_set("0", "9")
            + exp_char_set("a", "z")
            + exp_char_set("A", "Z")
            + "_"
        )
        k = 0

        lexeme.extend([prefix, peek(1)])
        k += 2

        while (char := peek(k)) != ">":
            if char in WORD:
                lexeme.append(char)
            else:
                raise InvalidRegex("Reference name contains invalid characters.")
            k += 1

        lexeme.append(char)
        consume_lexeme()

        return k + 1

    def is_escaped(pos):
        count = 0
        pos -= 1
        while pos >= 0 and regex[pos] == "\\":
            count += 1
            pos -= 1
        return count % 2 == 1

    def peek(offset):
        return regex[i + offset] if 0 < i + offset < len(regex) else ""

    while i < len(regex):
        char = regex[i]

        if char == "[":
            if is_escaped(i):
                lexeme.append(char)
            else:
                if is_char_class:
                    lexeme.append(f"\\{char}")
                elif peek(1) == "]":
                    # Skip empty character classes.
                    i += 2
                    continue
                else:
                    consume_lexeme()
                    lexemes.append(char)
                    is_char_class = not is_char_class

        elif char == "]":
            if is_escaped(i):
                lexeme.append(char)
            else:
                if is_char_class:
                    consume_lexeme()
                    lexemes.append(char)
                    is_char_class = not is_char_class
                else:
                    raise InvalidRegex(f"Inconsistent closing bracket at index {i}.")

        elif char == "{":
            if is_escaped(i):
                lexeme.append(char)
            else:
                if is_char_class:
                    lexeme.append(f"\\{char}")
                elif peek(-1) in "*+?}":
                    raise InvalidRegex(
                        f'Invalid quantifier precedence at index {i} >> "{regex[i - 1:i + 1]}".'
                    )
                else:
                    consume_lexeme()
                    lexemes.append(char)

        elif char == "}":
            if is_escaped(i):
                lexeme.append(char)
            else:
                if is_char_class:
                    lexeme.append(f"\\{char}")
                elif peek(1) != "" and peek(1) in "*+?{":
                    raise InvalidRegex(
                        f'Invalid quantifier precedence at index {i} >> "{regex[i - 1:i + 2]}".'
                    )
                else:
                    consume_lexeme()
                    bracket, quantifier = lexemes[-2], lexemes[-1]
                    parts = quantifier.split(",")

                    if (
                        bracket == "{"
                        and quantifier != ""
                        and all(part == "" or part.isdigit() for part in parts)
                        and len(parts) < 3
                    ):
                        if (
                            len(parts) == 2
                            and all(part.isdigit() for part in parts)
                            and int(parts[1]) < int(parts[0])
                        ):
                            raise InvalidRegex(
                                f"Interval quantifier bounds out of order at index {i} >> {regex[i - 4:i + 1]}."
                            )

                        lexemes.append(char)
                    else:
                        raise InvalidRegex(f"Invalid interval quantifier {quantifier}.")

        elif char == "(":
            if is_escaped(i):
                lexeme.append(char)
            else:
                if is_char_class:
                    lexeme.append(f"\\{char}")
                else:
                    consume_lexeme()
                    lexemes.append(char)

        elif char == ")":
            if is_escaped(i):
                lexeme.append(char)
            else:
                if is_char_class:
                    lexeme.append(f"\\{char}")
                else:
                    consume_lexeme()
                    lexemes.append(char)

        # === BACKREFERENCES ===
        elif char.isdigit():
            if is_escaped(i):
                raise InvalidRegex(
                    "Not supported, use `(?<alphanumeric>...)` to capture, and `$<alphanumeric>` to load instead."
                )
            else:
                lexeme.append(char)

        elif char == "?":
            if is_escaped(i):
                lexeme.append(char)
            else:
                if is_char_class:
                    lexeme.append(f"\\{char}")
                elif peek(-1) == "(" and not is_escaped(i - 1):
                    if peek(1) == "<":
                        consume_lexeme()
                        i += consume_reference(prefix=char)
                        continue
                    else:
                        raise InvalidRegex(
                            f"Question-mark construct not supported at {i} >> {regex[i - 1:i + 2]}."
                        )
                else:
                    consume_lexeme()
                    lexemes.append(char)

        elif char == "$":
            if is_escaped(i):
                lexeme.append(char)
            else:
                if is_char_class:
                    lexeme.append(f"\\{char}")
                else:
                    nextc = peek(1)
                    if nextc == "":
                        pass
                    elif nextc == "<":
                        consume_lexeme()
                        i += consume_reference(prefix=char)
                        continue
                    else:
                        raise InvalidRegex("Anchor `$` is not allowed.")

        # `^` (1) has a "quirk" when is inside `[]` and (2) has to be ignored when it is first.
        elif char == "^":
            if is_escaped(i):
                lexeme.append(char)
            else:
                if is_char_class:
                    if peek(-1) == "[" and not is_escaped(i - 1):
                        if peek(1) == "]":
                            lexemes.pop()
                            # Skip `[^]`.
                            i += 2
                            continue
                        consume_lexeme()
                        lexemes.append(char)
                    else:
                        lexeme.append(f"\\{char}")
                else:
                    if peek(-1) == "":
                        pass
                    else:
                        raise InvalidRegex("Anchor `^` is not allowed.")

        # `-` has a "quirk" when (1) is inside `[]` and (2) is between two ASCII characters.
        # [NOTE] The previous implementation didn't consider the "quirky" `-` as an isolated chunk.
        elif char == "-":
            if is_escaped(i):
                lexeme.append(char)
            else:
                if is_char_class:
                    low, up = peek(-1), peek(1)
                    if (
                        ord(low) < 128 and ord(up) < 128
                    ):  # Check if they're ASCII characters.
                        if lexeme:
                            if low == "[" or up == "]":
                                lexeme.append(f"\\{char}")
                            else:
                                lexeme.pop()
                                consume_lexeme()
                                lexemes += [low, char, up]
                                # Skip current `-` and upper bound `nextc`.
                                i += 2
                                continue
                        else:
                            lexeme.append(f"\\{char}")
                    else:
                        raise InvalidRegex(
                            f"Invalid ASCII boundaries in {regex[i - 1:i + 2]}"
                        )
                else:
                    lexeme.append(f"\\{char}")

        elif char == "|":
            if is_escaped(i):
                lexeme.append(char)
            else:
                if is_char_class:
                    lexeme.append(f"\\{char}")
                else:
                    consume_lexeme()
                    lexemes.append(char)

        elif char == ".":
            if is_escaped(i):
                lexeme.append(char)
            else:
                if is_char_class:
                    lexeme.append(f"\\{char}")
                else:
                    consume_lexeme()
                    lexemes.append(char)

        # === QUANTIFIERS ===
        # [NOTE] `?` is handled separately, since it could also act as a reference in `?<...>`.
        elif char in "+*":
            if is_escaped(i):
                lexeme.append(char)
            else:
                if is_char_class:
                    lexeme.append(f"\\{char}")
                else:
                    consume_lexeme()
                    lexemes.append(char)

        # === PREDEFINED CHARACTER CLASSES ===
        # Supported.
        elif char in "dDwWsSnt":
            if is_escaped(i):
                lexeme.pop()
                consume_lexeme()
                lexemes.append(f"\\{char}")
            else:
                lexeme.append(char)

        # Unsupported.
        # To do: bB; Maybe: ux; Deprecated: cfv0; Weird: r.
        elif char in "bBcfruvx0":
            if is_escaped(i):
                raise InvalidRegex(f"Escape character \\{char} is not supported.")
            else:
                lexeme.append(char)

        # === BACKSLASH ===
        # (1) If the character that comes after has no QUIRKS, then the escape will be ignored.
        # (2) Since escapes should be escaped if they're expected to be LITERAL with "\\\\" or r'\\',
        # then the escape will be ignored too.
        elif char == "\\":
            if is_escaped(i):
                lexeme.append(char)
            else:
                if peek(1) not in "dDwWsSnt" + "bBcfruvx0" + "|+*?-^$.()[]{}":
                    pass
                else:
                    lexeme.append(char)

        else:
            lexeme.append(char)

        i += 1

    consume_lexeme()

    return lexemes


def re_expand(re_chunks: list[str]):
    SPECIAL_CHARACTERS = "()[]{}|.*?+-"

    def peek(offset):
        return re_chunks[i + offset] if 0 < i + offset < len(re_chunks) else ""

    def exp_char_set(low: str, up: str) -> str:
        return "".join(chr(c) for c in range(ord(low), ord(up) + 1))

    def sub_exp_all(exp: str) -> str:
        return "".join([elem for elem in string.printable if elem not in exp])

    def add_ctx_esc(exp: str) -> str:
        result: list[str] = []

        for char in exp:
            if char in SPECIAL_CHARACTERS:
                result.append("\\")

            result.append(char)

        return "".join(result)

    def chain(x, *funcs):
        result = x
        for func in funcs:
            result = func(result)
        return result

    def del_ctx_esc(exp: str) -> str:
        result: list[str] = []

        for char in exp:
            if char in SPECIAL_CHARACTERS:
                result.pop()

            result.append(char)

        return "".join(result)

    DIGITS = exp_char_set("0", "9")
    NOT_DIGITS = add_ctx_esc(sub_exp_all(DIGITS))
    WORD = DIGITS + exp_char_set("a", "z") + exp_char_set("A", "Z") + "_"
    NOT_WORD = add_ctx_esc(sub_exp_all(WORD))
    SPACE = " \t\n\r\f\v"
    NOT_SPACE = add_ctx_esc(sub_exp_all(" "))
    WILDCARD = add_ctx_esc(sub_exp_all("\n"))

    lexemes: list[str] = []
    i = 0
    is_char_class = False
    is_negated = False

    while i < len(re_chunks):
        re_chunk = re_chunks[i]

        if re_chunk == "[":
            is_char_class = not is_char_class
            lexemes.append(re_chunk)

        elif re_chunk == "]":
            is_char_class = not is_char_class

            assembled: list[str] = []
            while lexemes and (lexeme := lexemes.pop()) != "[":
                assembled.append(lexeme)

            assert assembled, "Empty character class."

            asm_chunk = "".join(assembled[::-1])

            if is_negated:
                asm_chunk = chain(
                    asm_chunk,
                    del_ctx_esc,
                    sub_exp_all,
                    add_ctx_esc,
                )
                is_negated = not is_negated

            lexemes += ["[", asm_chunk, "]"]

        elif re_chunk == "^":
            is_negated = not is_negated

        # === CHARACTER RANGE EXPANSION ===
        elif re_chunk == "-":
            low, up = lexemes.pop(), peek(1)
            lexemes.append(exp_char_set(low, up))
            i += 2
            continue

        # === PREDEFINED CHARACTER CLASSES EXPANSION ===
        # [NOTE] PCCEs don't become literal inside brackets.
        elif re_chunk == "\\d":
            lexemes += [DIGITS] if is_char_class else ["[", DIGITS, "]"]

        elif re_chunk == "\\D":
            lexemes += [NOT_DIGITS] if is_char_class else ["[", NOT_DIGITS, "]"]

        elif re_chunk == "\\w":
            lexemes += [WORD] if is_char_class else ["[", WORD, "]"]

        elif re_chunk == "\\W":
            lexemes += [NOT_WORD] if is_char_class else ["[", NOT_WORD, "]"]

        elif re_chunk == "\\s":
            lexemes += [SPACE] if is_char_class else ["[", SPACE, "]"]

        elif re_chunk == "\\S":
            lexemes += [NOT_SPACE] if is_char_class else ["[", NOT_SPACE, "]"]

        # === WILDCARD EXPANSION ===
        elif re_chunk == ".":
            lexemes += ["[", WILDCARD, "]"]

        else:
            lexemes.append(re_chunk)

        i += 1

    return lexemes


def re_norm(re_chunks: list[str]):
    SPECIAL_CHARACTERS = "()[]{}|.*?+-"
    QUANTIFIERS = {
        "?": (["["], ["]"]),
        "+": (["{"], ["}"]),
        "*": (["{", "["], ["]", "}"]),
    }

    def peek(offset) -> str:
        return re_chunks[i + offset] if 0 < i + offset < len(re_chunks) else ""

    def del_ctx_esc(exp: str) -> str:
        result: list[str] = []

        for nextc in list(exp):
            prevc = result[-1] if result else ""

            if nextc in SPECIAL_CHARACTERS:
                # [CHECK] All special characters which were not isolated should be "contextually" escaped.
                assert prevc == "\\", "Special symbol was not escaped."
                result.pop()

            result.append(nextc)

        return "".join(result)

    def is_named_reference(chunk: str) -> bool:
        return (
            len(chunk) > 2 and chunk[0] in "$?" and chunk[1] == "<" and chunk[-1] == ">"
        )

    result: list[str] = []
    i = 0

    while i < len(re_chunks):
        re_chunk = re_chunks[i]

        # === CHARACTER CLASSES NORMALIZATION ===
        if re_chunk == "[":
            # [CHECK] Since a character class could contain predefined characters, then they'll
            # be isolated during the split pass, and expanded during the expand pass where they
            # get assembled into one chunk.
            assert peek(2) == "]", "`[...]` is not assembled."

            if os.getenv("PARSE_TESTS", 0):
                result += ["(", "|".join(f'"{c}"' for c in del_ctx_esc(peek(1))), ")"]
            else:
                result += [
                    item for c in del_ctx_esc(peek(1)) for item in (f'"{c}"', "|")
                ][:-1]

            i += 3
            continue

        # === QUANTIFIERS NORMALIZATION ===
        elif re_chunk in "*+?":
            open_br, close_br = QUANTIFIERS[re_chunk]
            prevc = result[-1]

            if prevc == ")":
                assembled, depth = [], -1

                while ((chunk := result.pop()) != "(") or depth != 0:
                    assembled.append(chunk)
                    depth += 1 if chunk == ")" else -1 if chunk == "(" else 0

                assembled.append(chunk)
                result += open_br + assembled[::-1] + close_br
            else:
                # [CHECK] If the previous chunk is not a ')', then it should be a terminal
                # chunk of exactly length one.
                assert (
                    len(prevc) == 3 and prevc.startswith('"') and prevc.endswith('"')
                ), "Quantifier was not preceded by a terminal character."

                result += open_br + [result.pop()] + close_br

        # === INTERVAL QUANTIFIERS NORMALIZATION ===
        elif re_chunk == "{":
            prevc, nextc = result[-1], peek(1).split(",")
            # [CHECK] Interval quantifier could either be `{x, y}`, `{x,}`, `{,y}` or `{x}`.
            assert len(nextc) <= 2, "Interval quantifier has invalid arguments."
            args = (nextc[0], nextc[1]) if len(nextc) == 2 else (nextc[0], nextc[0])
            req, max = (int(args[0]) if args[0] else 0), (
                int(args[1]) if args[1] else 0
            )
            opt = max - req

            if prevc == ")":
                assembled, depth = [], -1

                while result and (chunk := result.pop()) != "(" or depth != 0:
                    assembled.append(chunk)
                    depth += 1 if chunk == ")" else -1 if chunk == "(" else 0

                assembled.append(chunk)
                assembled.reverse()

                result += (
                    assembled * req + (["["] + assembled + ["]"]) * opt
                    if opt >= 0
                    else assembled * req + ["{", "["] + assembled + ["]", "}"]
                )
            else:
                # [CHECK] If the previous chunk is not a ')', then it should be a terminal
                # chunk of exactly length one.
                assert (
                    len(prevc) == 3 and prevc.startswith('"') and prevc.endswith('"')
                ), "Interval quantifier was not preceded by a terminal character."
                last = result.pop()
                result += (
                    [last] * req + ["[", last, "]"] * opt
                    if opt >= 0
                    else [last] * req + ["{", "[", last, "]", "}"]
                )

            i += 3
            continue

        else:
            # [CHECK] The control flow ordering in the current pass will make it
            # such that both `[]`, `{}` and `+*?` will be dealt with and converted accordingly.
            # [CHECK] There should be no `.-^$` which are already taken care of in the previous passes.
            assert (
                re_chunk not in "[]{}.-^$+*?"
            ), "Invalid symbols at normalization pass."

            if re_chunk in ["(", ")", "|"] or is_named_reference(re_chunk):
                result.append(re_chunk)
            else:
                no_esc_chunk = del_ctx_esc(re_chunk)
                if peek(1) in "{*?+":
                    result += [f'"{no_esc_chunk[:-1]}"'] + [f'"{no_esc_chunk[-1]}"']
                else:
                    result.append(f'"{no_esc_chunk}"')

        i += 1

    return result


def re_parse(lexeme: str):
    def chain(x, *funcs):
        result = x
        for func in funcs:
            result = func(result)
        return result

    return chain(lexeme, re_split, re_expand, re_norm)
