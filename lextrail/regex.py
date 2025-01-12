r"""
Certainly! Regular expressions (regex) have a variety of constructs that allow for powerful pattern matching. Here’s a comprehensive list of common regex constructs, including those you mentioned like `[]`, `{}`, and others:

### Basic Constructs

1. **Literal Characters:**
   - `a`, `b`, `c`, ...: Matches the exact character.

2. **Special Characters:**
   - `.`: Matches any single character except newline.
   - `\`: Escapes a special character, e.g., `\.` matches a literal period.

### Character Classes

3. **Character Sets (`[]`):**
   - `[abc]`: Matches any one of the characters `a`, `b`, or `c`.
   - `[^abc]`: Matches any character except `a`, `b`, or `c`.
   - `[a-z]`: Matches any lowercase letter from `a` to `z`.
   - `[A-Z]`: Matches any uppercase letter from `A` to `Z`.
   - `[0-9]`: Matches any digit from `0` to `9`.
   - `[a-zA-Z0-9]`: Matches any alphanumeric character.

4. **Predefined Character Classes:**
   - `\d`: Matches any digit (equivalent to `[0-9]`).
   - `\D`: Matches any non-digit (equivalent to `[^0-9]`).
   - `\w`: Matches any word character (alphanumeric + underscore, equivalent to `[a-zA-Z0-9_]`).
   - `\W`: Matches any non-word character (equivalent to `[^a-zA-Z0-9_]`).
   - `\s`: Matches any whitespace character (spaces, tabs, newlines).
   - `\S`: Matches any non-whitespace character.

### Quantifiers

5. **Quantifiers (`{}`):**
   - `a{3}`: Matches exactly 3 occurrences of `a`.
   # [NOTE] Need to implement `?` into `<>` in main parsing unit.
   - `a{2,4}`: Matches between 2 and 4 occurrences of `a`.
   - `a{2,}`: Matches 2 or more occurrences of `a`.

6. **Shorthand Quantifiers:**
   - `a?`: Matches 0 or 1 occurrence of `a` (optional).
   - `a+`: Matches 1 or more occurrences of `a`.
   - `a*`: Matches 0 or more occurrences of `a`.

### Grouping and Alternation

7. **Grouping (`()`):**
   - `(abc)`: Groups `a`, `b`, and `c` together.
   - `(a|b)`: Matches either `a` or `b`.

8. **Alternation (`|`):**
   - `a|b`: Matches either `a` or `b`.

### Anchors

9. **Anchors:**
   - `^`: Matches the start of a line.
   - `$`: Matches the end of a line.
   - `\b`: Matches a word boundary.
   - `\B`: Matches a non-word boundary.

### Lookahead and Lookbehind

10. **Lookahead and Lookbehind:**
    - `(?=...)`: Positive lookahead.
    - `(?!...)`: Negative lookahead.
    - `(?<=...)`: Positive lookbehind.
    - `(?<!...)`: Negative lookbehind.

### Escaping Special Characters

11. **Escaping Special Characters:**
    - `\.`, `\*`, `\+`, `\?`, `\^`, `\$`, `\[`, `\]`, `\{`, `\}`, `\|`, `\(`, `\)`: Matches the literal character.

### Examples

- `a[bc]+`: Matches `a` followed by one or more of `b` or `c`.
- `\d{3}-\d{2}-\d{4}`: Matches a Social Security Number format (e.g., `123-45-6789`).
- `(abc|def)`: Matches either `abc` or `def`.
- `^\d+`: Matches one or more digits at the start of a line.
- `\w+@\w+\.\w+`: Matches a simple email format (e.g., `user@domain.com`).

### Implementation Considerations

When implementing a regex to FSM converter, you need to handle these constructs appropriately. Here’s a brief outline of how to handle some of these constructs:

- **Character Sets (`[]`):** Create transitions for each character in the set.
- **Quantifiers (`{}`):** Use loops or recursive structures to handle the specified number of repetitions.
- **Grouping (`()`):** Treat the grouped expression as a sub-NFA and integrate it into the main NFA.
- **Alternation (`|`):** Create parallel paths in the NFA.
- **Anchors (`^`, `$`):** Ensure the NFA starts or ends at the appropriate positions.
- **Lookahead/Lookbehind:** These can be more complex and may require additional states or transitions.

By understanding and implementing these constructs, you can build a robust regex to FSM converter.
"""

import math
import string
from enum import Enum
from typing import Optional

# Added exceptions:
# Throw error for backreferences.
# Throw error for lookarounds.
# Throw error for unicode.
# Throw error for unescaped `/`.
# Throw error for invalid quantifier (includes only `{x?, y?}` with `x` and `y` integers,
# `{}` not allowed).
# Throw error for escaping `unescapable` escaped characters
from lextrail.exceptions import InvalidRegex

# [NOTE] Don't forget special characters, we parse considering to some special character
# `.` or `[`, `-`..
# One shouldn't forget that they could lose their meaning if they're escaped
# `\` + `special character`.
# Always check if such character is not ESCAPED before proceding.

# [NOTE] Should be all ASCII characters, keep it as such for now.
# List of all printable ASCII characters except newline
ALL_CHARACTERS = list(string.printable[:-5])  # Exclude newline, carriage return, etc.

# REGEX characters that have been escaped when out of context.
ESCAPED_REGEX_WHEN_NO_CTX = "()[]{}|.*?+-"


class DelimType(Enum):
    PARENTHESIS = 1
    BRACKETS = 2
    BRACES = 3


delim_dict = {
    "(": DelimType.PARENTHESIS,
    "[": DelimType.BRACKETS,
    "{": DelimType.BRACES,
}


# Finds out if some character is escaped.
def _is_escaped(regex_str: str, index: int) -> bool:
    if index < 0:
        return False
    j = 0
    while regex_str[index] == "\\":
        j += 1
        index -= 1
    return j % 2 != 0


def _is_valid_quantifier(content: str):
    # Check for {n} format.
    if "," not in content:
        # Must be a positive integer.
        return content.isdigit()

    # Check for {m,n}, {m,}, or {,n} format.
    parts = content.split(",")
    if len(parts) != 2:
        return False

    m, n = parts
    # Validate m and n.
    if not m and not n:
        return False

    # Validate m.
    if m and not m.isdigit():
        return False

    # Validate n.
    if n and not n.isdigit():
        return False

    # Convert to integers (empty strings are treated as 0 or infinity).
    m_val = int(m) if m else 0
    n_val = int(n) if n else float("inf")

    # Ensure m <= n.
    return m_val <= n_val


# [NOTE] Can use `re` package to validate the regex.
# No need to check for parenthesis coherence and syntactic correctness.
# [NOTE] Special characters inside `[]` are automatically escaped (apart from `[]` itself), nesting with `()` or `[]` is not allowed.
# [ALERT] Adding another `[]` inside `[]` results in UNDEFINED BEHAVIOR, thus it must be ESCAPED by the USER. Unfortunately, `re` package will not help. A warning should be emitted.
# [NOTE] Could remove the CF `if current:` through removing empty strings in a following pass.
# [NOTE] Lookahead and Lookbehind are still not supported.
# [NOTE] Special characters needs to be separated from terminals at this stage, or it'll lead to ambiguous splitting.
# Example: abc|\| -> ["abc", "|", "|"]
def _regex_split_pass(regex_str: str) -> list[str]:
    result: list[str] = []
    current: list[str] = []
    current_delimiter: Optional[DelimType] = None
    i = 0

    while i < len(regex_str):
        current_character: str = regex_str[i]

        # Escaped regex delimiters `\\(` and `\\)` are ignored.
        if current_character in "()[]{}" and not _is_escaped(regex_str, i - 1):
            # `{}` has an weird behavior, it's escaped automatically if it doesn't act as
            # a quantifier. To avoid such behavior, we'll throw an exception.
            if current_character == "}" and current_delimiter == DelimType.BRACES:
                if not _is_valid_quantifier("".join(current)):
                    raise InvalidRegex(f"{regex_str[:i+1]} is not a valid quantifier.")
            # Ignore capturing groups.
            if (
                current_character == "("
                and current_delimiter != DelimType.BRACKETS
                and i + 3 <= len(regex_str)
                and regex_str[i + 1 : i + 3] == "?:"
            ):
                if current:
                    result.append("".join(current))
                    current.clear()
                result.append(current_character)
                current_delimiter = delim_dict.get(current_character)
                i += 3
                continue
            # [TODO] Whenever forward accessing `i + x`, need to make sure that there is data.
            # [NOT SUPPORTED] Send exception for lookarounds.
            if (
                current_character == "("
                and current_delimiter != DelimType.BRACKETS
                and (
                    (
                        i + 3 <= len(regex_str)
                        and regex_str[i + 1 : i + 3] in ["?=", "?!"]
                    )
                    or (
                        i + 4 <= len(regex_str)
                        and regex_str[i + 1 : i + 4] in ["?<=", "?<!"]
                    )
                )
            ):
                raise InvalidRegex("Lookarounds are not supported yet.")
            # Leaving the scope.
            if current_character in ")]}":
                current_delimiter = None
            # Useful for detecting (range) character sets.
            current_delimiter = delim_dict.get(current_character, current_delimiter)
            # Avoids empty strings.
            if current:
                result.append("".join(current))
                current.clear()
            result.append(current_character)

        # [NOT SUPPORTED] Send exception for backreferences.
        elif current_character.isdigit() and _is_escaped(regex_str, i - 1):
            raise InvalidRegex("Backreferences are not supported yet.")

        # [NOT SUPPORTED] Send exception for unicode characters.
        elif current_character == "u" and _is_escaped(regex_str, i - 1):
            raise InvalidRegex("Unicode characters are not supported yet.")

        # Dealing with (range) character sets.
        elif current_character == "-" and not _is_escaped(regex_str, i - 1):
            if current_delimiter == DelimType.BRACKETS:
                # Makes sure there are characters between `-`.
                if current and regex_str[i + 1] != "]":
                    # Pop the start `0` in `[0-9]`.
                    current.pop()
                    # Avoids adding empty strings.
                    if current:
                        result.append("".join(current))
                        current.clear()
                    result.append(regex_str[i - 1 : i + 2])
                    # Skip the end `9` in `[0-9]`.
                    i += 2
                    continue
                else:
                    current.append("\\" + current_character)
            # [NOTE] Usually, it's easy to differentiate between a special `-` and a standard one,
            # since `[x-y]` is splitted as ["[", "x-y", "]"]. However, we'll escape it to have
            # consistency.
            else:
                if current:
                    result.append("".join(current))
                    current.clear()
                result.append("\\" + current_character)

        # Dealing with quantifiers.
        elif current_character in "*+?":
            if current_delimiter == DelimType.BRACKETS:
                current.append("\\" + current_character)  # Needs to be escaped.
            else:
                if not _is_escaped(regex_str, i - 1):
                    # `current` should be empty.
                    if result[-1] in ")]}":
                        result.append(current_character)
                    # [NOTE] If there is nothing before `*+?`, `re` will take care of that.
                    else:
                        if current:
                            result.extend(
                                [
                                    "".join(current[:-1]),
                                    "(",
                                    current[-1],
                                    ")",
                                    current_character,
                                ]
                            )
                            current.clear()
                        # [NOTE] We can separate special characters into two categories,
                        # (1) are escaped and single which are "()[]{}|.-", those are
                        # "contextually" escaped but also are "single" (they're not grouped with other
                        # characters). (2) are "contextually" escaped, but can be grouped with other characters
                        # which are "/-". (1) are found in result while (2) are found in current.
                        # If the last character is a (1), but
                        # without `()[]{}` (dealt with above) as well as `|` (leads to an error if precedented with
                        # `*+?`), only `.` remains then.
                        # `.` will be replaced by [..], wrapping with `(..)` is useless.
                        else:
                            assert result[-1] == ".", "Only `.` character is allowed."
                else:
                    current.append(current_character)

        # Send exception if `/` is not escaped.
        elif current_character == "/" and not _is_escaped(regex_str, i - 1):
            if current_delimiter == DelimType.BRACKETS:
                current.append("\\" + current_character)  # Needs to be escaped.
                i += 1
                continue
            else:
                raise InvalidRegex(f"`/` must be escaped in {regex_str[:i+1]} ")

        # Send exception if `unescapable` characters are escaped.
        # Escapable characters `.^$*+?|()[]{}\\/dDwWsSntru` or digits.
        # [TODO] Is the list complete?
        elif (
            current_character == "\\"
            and not _is_escaped(regex_str, i - 1)
            and regex_str[i + 1] not in ".^$*+?|()[]{}\\/dDwWsSntru"
        ):
            # Backreferences are handled elsewhere.
            if not regex_str[i + 1].isdigit():
                raise InvalidRegex(
                    f"{regex_str[i + 1]} must not be escaped in {regex_str[:i+2]} "
                )

        # (1) Dealing with character classes.
        # (2) Dealing with newlines `\n`, tabs `\t` and carriage return `\r`.
        # [NOTE] Character classes and `\n`, `\t`,`\r` sustain behavior inside `[]`.
        # [NOTE] Correct for any valid (`.^$*+?|()[]{}\\/dDwWsSnt`) escaped character.
        elif current_character in "dDwWsSntr" and _is_escaped(regex_str, i - 1):
            # [NOTE] Ignoring `\d\D\w\W\s\S` as special characters inside a `[]`.
            # [NOTE] They shouldn't be ignored.
            # if current_delimiter == DelimType.BRACKETS:
            #     current.append("\\" + current_character)  # Needs to be escaped.
            #     i += 1
            #     continue
            # Avoids empty characters.
            if current[:-1]:
                result.append("".join(current[:-1]))
            result.append("".join([current[-1], current_character]))
            current.clear()

        # Dealing with special characters `.|`.
        elif current_character in ".|" and not _is_escaped(regex_str, i - 1):
            # [NOTE] Ignoring `.|` as special characters inside a `[]`.
            if current_delimiter == DelimType.BRACKETS:
                current.append("\\" + current_character)  # Needs to be escaped.
                i += 1
                continue
            # Avoids adding empty strings.
            if current:
                result.append("".join(current))
                current.clear()
            result.append(current_character)

        # [???] Dealing with anchors, they're irrelevant in our context. CFGs are expected to have deterministic properties.
        # [???] If user asks for a `regex("example")` in a CFG, it is equivalent
        # to regex("^example$").
        elif current_character in "^" and current_delimiter == DelimType.BRACKETS:
            if regex_str[i - 1] == "[" and not _is_escaped(regex_str, i - 2):
                assert len(current) == 0, "`current` should be empty."
                result.append(current_character)
            else:
                current.append("\\" + current_character)  # Needs to be escaped.

        elif current_character in "^$" and not _is_escaped(regex_str, i - 1):
            i += 1
            continue

        else:
            current.append(current_character)

        i += 1

    if current:
        result.append("".join(current))

    return result


# We'll reduce (range) character sets.
# Example: [0-9] -> [0123456789].
def _exp_char_set(low: str, up: str) -> str:
    return "".join(chr(c) for c in range(ord(low), ord(up) + 1))


# Negate an expression.
# Example: [^abc] -> [everything but abc]
def _sub_exp_all(exp: str) -> str:
    return "".join([elem for elem in ALL_CHARACTERS if elem not in exp])


# [NOTE] There is NO need to reason about negation of subexpressions such as [^abc] and [a^(subexp)bc],
# (1) everything inside `[]` is literal and (2) `^` has only a meaning at the beginning of a `[]`.
# Expand:
# (1) (range) Character sets.
# Example: [0-9] -> [0123456789].
# (2) Predefined character classes.
# (3) Special character `.`.
def _regex_expand_pass(regex_chunks: list[str]):
    expanded: list[str] = []
    i = 0

    while i < len(regex_chunks):
        current_chunk: str = regex_chunks[i]
        # Expand predefined character classes.
        if (
            len(current_chunk) == 2
            and current_chunk[0] == "\\"
            and current_chunk[1] in "dDwWsS"
        ):
            # Matches any digit (equivalent to `[0-9]`).
            if current_chunk[1] == "d":
                expanded = expanded + ["[", _exp_char_set("0", "9"), "]"]

            # Matches any non-digit (equivalent to `[^0-9]`).
            elif current_chunk[1] == "D":
                expanded = expanded + ["[", _sub_exp_all(_exp_char_set("0", "9")), "]"]

            # Matches any word character (alphanumeric + underscore, equivalent to `[a-zA-Z0-9_]`).
            elif current_chunk[1] == "w":
                expanded = expanded + [
                    "[",
                    _exp_char_set("a", "z")
                    + _exp_char_set("A", "Z")
                    + _exp_char_set("0", "9")
                    + "_",
                    "]",
                ]

            # Matches any non-word character (equivalent to `[^a-zA-Z0-9_]`).
            elif current_chunk[1] == "w":
                expanded = expanded + [
                    "[",
                    _sub_exp_all(
                        _exp_char_set("a", "z")
                        + _exp_char_set("A", "Z")
                        + _exp_char_set("0", "9")
                        + "_"
                    ),
                    "]",
                ]

            # Matches any whitespace character (spaces, tabs, newlines).
            elif current_chunk[1] == "s":
                expanded = expanded + [" ", "|", "\t", "|", "\n"]

            # Matches any non-whitespace character.
            elif current_chunk[1] == "S":
                expanded = expanded + ["[", "".join(ALL_CHARACTERS), "]"]

        # Expand special characters.
        # Expand special character `.`.
        # [TODO] Does `ALL_CHARACTERS` map to all possible characters?
        elif len(current_chunk) == 1 and current_chunk[0] == ".":
            expanded = expanded + ["[", "".join(ALL_CHARACTERS), "]"]

        # After expanding (range) character sets.
        # Since they get isolated in the split pass, they should be concatenated
        # with the other chunks.
        elif len(current_chunk) == 1 and current_chunk[0] == "]":
            assembled: list[str] = []
            j = len(expanded) - 1
            while expanded[j] != "[":
                assembled.append(expanded[j])
                expanded.pop()
                j -= 1
            # Avoids empty string.
            if assembled:
                expanded.append("".join(assembled[::-1]))
            expanded.append("]")

        # Expand special character `-`.
        # [NOTE] Need to distinguish if it's `-` inside `[]` or outside.
        # -> `-` is escaped with `\` when it's outside `[]` during split pass.
        elif len(current_chunk) == 3 and current_chunk[1] == "-":
            expanded = expanded + [_exp_char_set(current_chunk[0], current_chunk[2])]

        else:
            expanded.append(current_chunk)

        i += 1

    return expanded


def _add_context_escapes(regex_chunk: str) -> str:
    result: list[str] = []
    i = 0

    while i < len(regex_chunk):
        current_character = regex_chunk[i]

        # [NOTE] Condition (2) is important, during the last pass, we remove the escapes and if
        # `\\` which comes from the negation is not escaped, it's going to be removed.
        # It may seems repetitive, since we could get rid of the escapes in this pass,
        # however, the last pass should have context from the escapes to function correctly
        # or it'll lead to undefined behavior.
        if current_character in ESCAPED_REGEX_WHEN_NO_CTX or current_character == "\\":
            result.append("\\")

        result.append(current_character)
        i += 1

    return "".join(result)


def _del_context_escapes(regex_chunk: str) -> str:
    result: list[str] = []
    i = 0

    while i < len(regex_chunk):
        current_character = regex_chunk[i]

        if current_character in ESCAPED_REGEX_WHEN_NO_CTX and _is_escaped(
            regex_chunk, i - 1
        ):
            result.pop()

        result.append(current_character)
        i += 1

    return "".join(result)


def _regex_negate_pass(regex_chunks: list[str]) -> list[str]:
    negated: list[str] = []
    i = 0

    while i < len(regex_chunks):
        current_chunk: str = regex_chunks[i]
        if current_chunk[0] == "^" and regex_chunks[i - 1] == "[":
            # [NOTE] If context is not disabled during the negation pass, the context
            # is going to be ruined. Since the next steps need the context,
            # it'll lead to incorrect behavior.
            negated.append(
                _add_context_escapes(_sub_exp_all(_del_context_escapes(current_chunk)))
            )
        else:
            negated.append(current_chunk)
        i += 1

    return negated


# [NOTE] When turning things into terminals, there'll be escapes.
# (1) We deal with this here, '\\[' will be '"["' and not '"\\["'.
# (2) We deal with this in the main parsing unit, terminals will automatically deal with
# escaped characters (better).
def _regex_normalize_pass(regex_chunks: list[str]):
    result: list[str] = []
    i = 0

    while i < len(regex_chunks):
        current_chunk: str = regex_chunks[i]

        # Converting [abcd] to (a|b|c|d).
        if current_chunk == "[":
            # `[` and `]` get replaced by `(` and `)`.
            result.append("(")
            # The elements should already be assembled in the expand pass.
            assert (
                regex_chunks[i + 1] == "]" or regex_chunks[i + 2] == "]"
            ), "`[]` was not assembled."
            if regex_chunks[i + 1] != "]":
                assembled: list[str] = []
                j = 0
                while j < len(regex_chunks[i + 1]):
                    current_character = regex_chunks[i + 1][j]
                    # [TODO] There is a problem here, normally when I expand inside [..], I add
                    # specific escapes that have a meaning to the parser. However, if ^ is applied,
                    # then it needs to be applied carefully. Also normalizing should be carefull
                    # aswell. Here I think I'm dealing with my own escaped but when they come for
                    # negate, it's undefined behavior.
                    if current_character == "\\":
                        assembled.append(regex_chunks[i + 1][j : j + 2])
                        j += 2
                        continue
                    else:
                        assembled.append(current_character)
                        j += 1
                result.append("|".join(assembled))
                result.append(")")
                i += 3
                continue
            else:
                result.append(")")
                i += 2

        elif current_chunk == "{":
            # Exception will be raised if a quantifier `{}` is empty or
            # not in the correct format `{x?, y?}`/`{x}`.
            interval = regex_chunks[i + 1].split(",")
            if len(interval) == 2:
                min, max = interval
                min = int(min) if min else 0
                max = int(max) if max else math.inf
            else:
                min = int(interval[0])
                max = 0
            # [NOTE] Having a `*+?` before `{` will lead to a syntactic error,
            # detectable with `re`.
            if result[-1] == ")":
                stack_idx = 0
                start_idx = 0
                for idx in reversed(range(len(result[:-1]))):
                    if result[idx] == "(":
                        if stack_idx != 0:
                            stack_idx -= 1
                        else:
                            start_idx = idx
                            break
                    elif result[idx] == ")":
                        stack_idx += 1
                length = len(result[start_idx:])
                for _ in range(min - 1):
                    result.extend(result[start_idx : start_idx + length])
                if max != math.inf:
                    # There is always an instance, if `min` is 0,
                    # then reuse for max.
                    if min == 0:
                        result.append("?")
                        max -= 1
                    for _ in range(max):  # type: ignore
                        result.extend(result[start_idx : start_idx + length])
                        result.append("?")
                else:
                    # `min` can't be 0, {,} is invalid and it'll throw an exception.
                    result.extend(result[start_idx : start_idx + length])
                    result.append("*")
                i += 3
                continue
            else:
                result[-1] += result[-1][-1] * min
                if max != math.inf:
                    result.extend(["(", result[-1][-1], ")", "?"] * (max - 1))  # type: ignore
                else:
                    result.extend(["(", result[-1][-1], ")", "*"])  # type: ignore
                i += 3
                continue

        else:
            result.append(current_chunk)
        i += 1

    return result


def _is_chunk_pipe(regex_chunk: str) -> bool:
    i = 0

    while i < len(regex_chunk):
        if regex_chunk[i] == "|" and not _is_escaped(regex_chunk, i - 1):
            return True

        i += 1

    return False


def _split_pipe(pipe_chunk: str) -> list[str]:
    current: list[str] = []
    result: list[str] = []
    i = 0

    while i < len(pipe_chunk):
        current_character = pipe_chunk[i]

        if current_character == "|" and not _is_escaped(pipe_chunk, i - 1):
            result.append('"' + "".join(current) + '"')
            current.clear()

        elif current_character == "\\" and not _is_escaped(pipe_chunk, i - 1):
            i += 1
            continue

        else:
            current.append(current_character)

        i += 1

    result.append('"' + "".join(current) + '"')

    return result


def _discard_escapes(regex_chunk: str) -> str:
    result: list[str] = []
    i = 0

    while i < len(regex_chunk):
        current_character = regex_chunk[i]

        if current_character == "\\" and not _is_escaped(regex_chunk, i - 1):
            i += 1
            continue

        else:
            result.append(current_character)

        i += 1

    return "".join(result)


def _regex_terminalize_pass(regex_chunks: list[str]):
    result: list[str] = []
    i = 0

    while i < len(regex_chunks):
        current_chunk = regex_chunks[i]

        if current_chunk in "()|*?+":
            result.append(current_chunk)

        elif _is_chunk_pipe(current_chunk):
            result.append("|".join(_split_pipe(current_chunk)))

        else:
            result.append('"' + _discard_escapes(current_chunk) + '"')

        i += 1

    return result
