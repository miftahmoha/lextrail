from cfg_parse.exceptions import InvalidDelimiters


def _map_opening_delim_idx_to_its_enclosing_delim_idx(
    definition: str, opening_delim_index: int
) -> int:
    count = 1

    for i, char in enumerate(definition[opening_delim_index:]):
        if char == "(":
            count += 1
        elif char == ")":
            count -= 1
            if count == 0:
                return i + opening_delim_index

    raise InvalidDelimiters("No matching closing parenthesis found")


# Separates the Regex(...) expressions from the other parts of the definition.
def _separate_regex_substrings(definition: str) -> list[str]:
    parts: list[str] = []

    while 'Regex("' in definition:
        start = definition.index('Regex("')
        if start > 0:
            parts.append(definition[:start])
        end = _map_opening_delim_idx_to_its_enclosing_delim_idx(
            definition, start + len('Regex("')
        )
        parts.append(definition[start : end + 1])
        definition = definition[end + 1 :]

    if definition:
        parts.append(definition)

    return parts


def _convert_to_lark_syntax(custom_syntax: str):
    lines: list[str] = custom_syntax.split("\n")
    lark_syntax: list[str] = []

    for line in lines:
        if not line:
            # Skip empty lines.
            continue

        parts = _separate_regex_substrings(line)
        lark_line: list[str] = []
        for part in parts:
            if 'Regex("' in part:
                start = part.index('Regex("') + len('Regex("')
                end = _map_opening_delim_idx_to_its_enclosing_delim_idx(part, start) - 1
                regex_content = part[start:end]
                lark_subline = part.replace(
                    f'Regex("{regex_content}")', f"/{regex_content}/"
                )
                lark_line.append(lark_subline)
            else:
                lark_subline = part
                lark_subline = lark_subline.replace("{", "(").replace("}", ")*")
                lark_subline = lark_subline.replace("[", "(").replace("]", ")?")
                lark_line.append(lark_subline)
        lark_syntax.append("".join(lark_line))

    return "\n".join(lark_syntax)


def convert_to_custom_syntax(lark_syntax: str):
    return NotImplemented
