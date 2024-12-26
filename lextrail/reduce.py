def is_subexpression_from_end(main_list, sub_list):
    """
    Check if any prefix of sub_list is a subexpression from the end of main_list.

    Args:
    main_list (list): The main list to search in
    sub_list (list): The list potentially containing a subexpression

    Returns:
    bool: True if a subexpression from sub_list is found at the end of main_list
    """
    # Try all prefixes of sub_list
    for i in range(len(sub_list), 0, -1):
        candidate = sub_list[:i]
        if len(candidate) > len(main_list):
            continue

        # Check if candidate matches the end of main_list
        if main_list[-len(candidate) :] == candidate:
            return candidate

    return None


# Example usage
a = ["factor", "-", "number", "/"]
b1 = ["number", "/"]
b2 = ["number", "/", "test", "whatever", "..."]
c = ["factor", "-"]

# print(is_subexpression_from_end(a, b1))  # True
# print(is_subexpression_from_end(a, b2))  # True
# print(is_subexpression_from_end(a, c))  # False

import re

# regex = "factor \+ (term " - "\s*)*"
# subexp = '(term "-" )'
# pattern = rf"({subexp})\*$"
# print(re.search(pattern, regex))


def check_end_subexpression(regex, subexp):
    # Escape special regex characters in the subexpression
    escaped_subexp = re.escape(subexp)

    # Create a pattern that matches the subexpression at the end
    pattern = f".*{escaped_subexp}$"

    # Check if the subexpression is at the end
    return bool(re.search(pattern, regex))


# Example usage
regex = 'factor \+ (term "-"\s)*'
subexp = 'term "-" '

print(check_end_subexpression(regex, subexp))


def check_end_subexpression(regex, subexp):
    # Escape the subexpression to handle special regex characters
    escaped_subexp = re.escape(subexp)

    # Pattern to match the subexpression at the end inside a * quantifier
    pattern = f"\\({escaped_subexp}\\)\\*$"

    return bool(re.search(pattern, regex))


# Example usage
regex = 'factor "+" (term "-")*'
subexp = 'term "-"'

print(check_end_subexpression(regex, subexp))

# pattern = r'factor "\+" (term "-")*'
pattern = r'factor "\+" (term "-" (term "-")*)?'
pattern = r'factor "\+"( term "-"( term "-")*)?'


# Test cases
test_strings = [
    r'factor "+"',
    r'factor "+" term "-"',
    r'factor "+" term "-"term "-"',
    r'factor "+" term "-" term "-" term "-" term "-"',
]

for s in test_strings:
    print(f"{s}: {bool(re.match(pattern, s))}")
