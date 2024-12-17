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

from typing import Optional
from enum import Enum
import string


# [NOTE] Don't forget special characters, we parse considering to some special character
# `.` or `[`, `-`..
# One shouldn't forget that they could lose their meaning if they're escaped
# `\` + `special character`.
# Always check if such character is not ESCAPED before proceding.

# [NOTE] Should be all ASCII characters, keep it as such for now.
# List of all printable ASCII characters except newline
ALL_CHARACTERS = list(string.printable[:-5])  # Exclude newline, carriage return, etc.


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
# [NOTE] To be implemented for splitter in main parsing unit.
def is_escaped(regex_str: str, index: int) -> bool:
    if index < 0:
        return False
    j = 0
    while regex_str[index] == "\\":
        j += 1
        index -= 1
    return j % 2 != 0


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
        if current_character in "()[]{}" and not is_escaped(regex_str, i - 1):
            # [NOTE] Escaping `(){}` inside a `[]`, nested `[]` leads to UNDEFINED BEHAVIOR in `re`, thus it must be escaped by the user.
            if (
                current_delimiter == DelimType.BRACKETS
                and current_character not in "[]"
            ):
                # Escape all delimiters inside `[]`.
                current.append("\\" + current_character)  # Needs to be escaped.
                i += 1
                continue
            # Leaving the scope.
            if current_character in ")]}":
                current_delimiter = None
            # Useful for detecting (range) character sets.
            current_delimiter = delim_dict.get(current_character, current_delimiter)
            # [NOTE] Could be optimized to avoid CF on every iteration.
            if current:
                result.append("".join(current))
                current.clear()
            result.append(current_character)
        # Dealing with (range) character sets.
        elif (
            current_character == "-"
            and current_delimiter == DelimType.BRACKETS
            and not is_escaped(regex_str, i - 1)
        ):
            if current_delimiter == DelimType.BRACKETS:
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
            # We need to separate between `-` that are inside `[]` and the ones outside.
            # We'll escape the ones outside.
            else:
                if current:
                    result.append("".join(current))
                    current.clear()
                result.append("\\" + current_character)
        # Dealing with quantifiers.
        elif current_character in "*+?" and regex_str[i - 1] in ")]}":
            # [NOTE] Ignoring `*+?` as special characters inside a `[]`.
            if current_delimiter == DelimType.BRACKETS:
                current.append("\\" + current_character)  # Needs to be escaped.
                i += 1
                continue
            result.append(current_character)
        # (1) Dealing with character classes.
        # (2) Dealing with newlines `\n` and tabs `\t`.
        elif current_character in "dDwWsSnt" and is_escaped(regex_str, i - 1):
            # [NOTE] Ignoring `\d\D\w\W\s\S` as special characters inside a `[]`.
            if current_delimiter == DelimType.BRACKETS:
                current.append("\\" + current_character)  # Needs to be escaped.
                i += 1
                continue
            result.append("".join(current[:-1]))
            result.append("".join([current[-1], current_character]))
            current.clear()
        # Dealing with special characters `.*+?|`.
        elif current_character in ".*+?|" and not is_escaped(regex_str, i - 1):
            # [NOTE] Ignoring `.*+?|` as special character inside a `[]`.
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
        # [FIX] Needs to be fixed, it gets ignored when it shouldn't.
        # -> Should be ignored if not escaped, the only case when it's not the case is the one below:
        elif current_character in "^" and current_delimiter == DelimType.BRACKETS:
            if regex_str[i - 1] == "[" and not is_escaped(regex_str, i - 2):
                # `current` should be empty.
                result.append(current_character)
            else:
                current.append("\\" + current_character)  # Needs to be escaped.
        elif current_character in "^$" and not is_escaped(regex_str, i - 1):
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
                # [NOTE] Need to implement `\n` and `\t` in main parsing unit.
                expanded = expanded + [" ", "|", "\t", "|", "\n"]
            # Matches any non-whitespace character.
            elif current_chunk[1] == "S":
                expanded = expanded + ["[", "".join(ALL_CHARACTERS), "]"]
        # Expand special characters.
        # Expand special character `.`.
        elif len(current_chunk) == 1 and current_chunk[0] == ".":
            expanded = expanded + ["(", "".join(ALL_CHARACTERS), ")"]
        # After expanding (range) character sets, (since they get isolated in the split pass) they should be concatenated with the other chunks.
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


def _regex_negate_pass(regex_chunks: list[str]) -> list[str]:
    negated: list[str] = []
    i = 0

    while i < len(regex_chunks):
        current_chunk: str = regex_chunks[i]
        if current_chunk[0] == "^" and regex_chunks[i - 1] == "[":
            negated.append(_sub_exp_all(current_chunk))
        else:
            negated.append(current_chunk)
        i += 1

    return negated


# [NOTE] When turning things into terminals, there'll be escapes.
# (1) We deal with this here, '\\[' will be '"["' and not '"\\["'.
# (2) We deal with this in the main parsing unit, terminals will automatically deal with
# escaped characters (better).
def convert_regex_to_custom_syntax(regex: str):
    pass


print(_split_regex(r"(^abc{2,4}. [^era-z(testescape).t*] (f\wg)* \\\(lol\))"))
