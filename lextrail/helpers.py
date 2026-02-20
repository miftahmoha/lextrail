import os

from collections import deque
from typing import TYPE_CHECKING, Deque

if TYPE_CHECKING:
    from lextrail.build import Symbol, SymbolGraph


class TrailError(Exception):
    pass


def consume_lexeme(lexemes: list[str], accumulate: list[str]):
    if accumulate:
        lexemes.append("".join(accumulate))
        accumulate.clear()


def is_escaped(input: list[str], index: int) -> bool:
    count = 0
    index -= 1
    while index >= 0 and input[index] == "\\":
        count += 1
        index -= 1
    return count % 2 == 1


def peek(input: list[str], index: int, offset: int) -> str:
    return input[index + offset] if 0 <= index + offset < len(input) else str()


class TrailContext:
    def __init__(self, **env):
        self.env = env

    def __enter__(self):
        self.original = {key: os.getenv(key) for key in self.env}
        os.environ.update(self.env)

    def __exit__(self, *args):
        for k, v in self.original.items():
            if v is None:
                del os.environ[k]
            else:
                os.environ[k] = v


def contains_special_characters(input: str):
    return any(character in "[@!#$%^&*()<>?/\\|}~:" for character in input)


def bfs(graph: "SymbolGraph", start: list["Symbol"]) -> list["Symbol"]:
    visited = []

    queue: Deque["Symbol"] = deque()
    queue.extend(start)

    while queue:
        vertex = queue.popleft()
        if vertex not in visited:
            visited.append(vertex)
            queue.extend(graph.edges[vertex])

    return visited


def format_error(header: str, context: str, source: str) -> str:
    RED = "\x1b[31m"
    BLUE = "\x1b[34m"
    YELLOW = "\x1b[33m"
    BOLD = "\x1b[1m"
    RESET = "\x1b[0m"

    markers = ("." * len(context), "^" * len(source))

    return (
        f"{BOLD}{RED}error{RESET}: {header}\n"
        f"{BOLD}{BLUE}  |{RESET}\n"
        f"{BOLD}{BLUE}  |{RESET} {context}{source}\n"
        f"{BOLD}{BLUE}  |{RESET} {BOLD}{YELLOW}{markers[0]}{BOLD}{RED}{markers[1]}{RESET}"
    )
