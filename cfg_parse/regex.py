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

from typing import Deque, Optional
from enum import Enum
import string

# [NOTE] Don't forget special characters, we parse considering to some special character
# `.` or `[`, `-`..
# One shouldn't forget that they could lose their meaning if they're escaped
# `\` + `special character`.
# Always check if such character is not ESCAPED before proceding.

"""
Dealing with 

`.` : Matches any single character except newline.
"""

# List of all printable ASCII characters except newline
ALL_CHARACTERS = list(string.printable[:-5])  # Exclude newline, carriage return, etc.


def format_characters(characters: list[str]):
    """Formats a list of characters into a string with each character enclosed in "" and separated by |."""
    return "|".join(f'"{char}"' for char in characters)


"""
Dealing with 

[abc]: Matches any character except a, b, or c.
"""


"""
Dealing with 

[^abc]: Matches any character except a, b, or c.
"""


# Not that simple, recursive nature,`a` could be a subexpression.
def format_w_exclusion(excluded: Optional[list[str]] = None):
    """Formats the ALL_CHARACTERS list into a string with each character enclosed in "" and separated by |,
    excluding the specified characters."""
    return (
        format_characters(ALL_CHARACTERS)
        if excluded
        else format_characters(
            [char for char in ALL_CHARACTERS if char not in excluded]
        )
    )


class DelimType(Enum):
    PARENTHESIS = 1
    BRACKETS = 2
    BRACES = 3


# Finds out if some character is escaped.
# [NOTE] To be implemented for CFG splitter!
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
def _split_regex(regex_str: str) -> list[str]:
    result = []
    current = []
    current_delimiter: Optional[DelimType] = None
    i = 0

    while i < len(regex_str):
        current_character: str = regex_str[i]

        # Escaped regex delimiters `\\(` and `\\)` are ignored.
        if current_character in "()[]{}" and not is_escaped(regex_str, i - 1):
            # Useful for detecting (range) character sets.
            if current_character == "(":
                current_delimiter = DelimType.PARENTHESIS
            elif current_character == "[":
                current_delimiter = DelimType.BRACKETS
            else:
                current_delimiter = DelimType.BRACES
            # [NOTE] Could be optimized to avoid CF on every iteration.
            if current:
                result.append("".join(current))
                current.clear()
            result.append(current_character)
        # Dealing with (range) character sets, we'll reduce them.
        # Example: [0-9] -> [0123456789].
        elif (
            current_character == "-"
            and current_delimiter == DelimType.BRACKETS
            and not is_escaped(regex_str, i - 1)
        ):
            # Pop the start `0` in `[0-9]`.
            current.pop()
            # Avoids adding empty strings.
            if current:
                result.append("".join(current))
                current.clear()
            # [NOTE] Do it in a new function called canonicalize?
            # result.append(
            #     "".join(
            #         chr(c)
            #         for c in range(ord(regex_str[i - 1]), ord(regex_str[i + 1]) + 1)
            #     )
            # )
            result.append(regex_str[i - 1 : i + 2])
            # Skip the end `9` in `[0-9]`.
            i += 2
            continue
        # Dealing with quantifiers.
        elif current_character in "*+?" and regex_str[i - 1] in ")]}":
            result.append(current_character)
        # Dealing with character classes.
        elif current_character in "dDwWsS" and is_escaped(regex_str, i - 1):
            result.append("".join(current[:-1]))
            result.append("".join([current[-1], current_character]))
            current.clear()
        # Dealing with special characters.
        elif current_character == "." and not is_escaped(regex_str, i - 1):
            # Avoids adding empty strings.
            if current:
                result.append("".join(current))
                current.clear()
            result.append(current_character)
        # Dealing with anchors, they're irrelevant in our context.
        # [NOTE] If user asks for a `regex("example")` in a CFG, it is equivalent
        # to regex("^example$").
        elif current_character in "^$" and not is_escaped(regex_str, i - 1):
            i += 1
            continue
        else:
            current.append(current_character)
        i += 1

    if current:
        result.append("".join(current))

    return result


def cannonicalize(regex_str: list[str]):
    pass


def convert_regex_to_custom_syntax(regex: str):
    pass


print(_split_regex(r"(^abc{2,4} [era-z.t*]  (f\wg)* \\\(lol\))"))
