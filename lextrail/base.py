import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from itertools import chain
from typing import Any


class Symbol_Kind(Enum):
    NONE = 1
    TERMINAL = 2
    VARIABLE = 3
    REGEX = 4
    REFERENCE = 5
    END = 6
    SPECIAL = 7


@dataclass(slots=True)
class Symbol:
    content: str = ""
    kind: Symbol_Kind = Symbol_Kind.NONE
    id: uuid.UUID = field(default_factory=lambda: uuid.uuid4())
    tags: list[str] = field(default_factory=list)

    def __hash__(self):
        return hash(self.id)

    def __bool__(self):
        return self.kind != Symbol_Kind.NONE

    def serialize(self):
        return {
            # `label` is the convention used by Viz.
            "label": self.content,
            "id": str(self.id),
            "kind": str(self.kind),
        }


@dataclass(slots=True)
class SymbolGraph:
    initials: list[Symbol] = field(default_factory=list)
    tree: dict[Symbol, list[Symbol]] = field(default_factory=lambda: defaultdict(list))
    finals: list[Symbol] = field(default_factory=list)

    def __eq__(self, other) -> bool:
        if isinstance(other, SymbolGraph):
            return (
                (self.initials == other.initials)
                and (self.tree == other.tree)
                and (self.finals == other.finals)
            )
        return NotImplemented

    def __bool__(self) -> bool:
        return bool(self.initials) and bool(self.tree) and bool(self.finals)

    @property
    def symbols(self):
        return set(chain(self.initials, *self.tree.values()))

    def serialize(self) -> dict[str, Any]:
        nodes = [symbol.serialize() for symbol in self.symbols]

        edges = [
            {"from": str(symbol.id), "to": str(successor.id), "color": "gray"}
            for symbol, successors in self.tree.items()
            for successor in successors
        ]

        return {"nodes": nodes, "edges": edges}

    def copy(self):
        return SymbolGraph(
            initials=self.initials.copy(),
            tree=self.tree.copy(),
            finals=self.finals.copy(),
        )
