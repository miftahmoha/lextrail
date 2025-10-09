import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from itertools import chain
from typing import Any, TypeVar

T = TypeVar("T")


class SymbolType(Enum):
    NONE = 0
    TERMINAL = 1
    NON_TERMINAL = 2
    REGEX = 3
    SPECIAL = 4
    REFERENCE = 5


@dataclass(slots=True)
class Symbol:
    content: str = ""
    s_type: SymbolType = SymbolType.NONE
    s_id: uuid.UUID = field(default_factory=lambda: uuid.uuid4())
    s_metadata: dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.s_id)

    def __bool__(self):
        return self.s_type != SymbolType.NONE

    def serialize(self):
        return {
            # `label` is the convention used by Viz.
            "label": self.content,
            "id": str(self.s_id),
            "type": str(self.s_type),
        }


class SymbolGraphType(Enum):
    STANDARD = 1
    NONE_ANY = 2
    ONCE_ANY = 3
    NONE_ONCE = 4


@dataclass(slots=True)
class SymbolGraph:
    initials: list[Symbol] = field(default_factory=list)
    tree: dict[Symbol, list[Symbol]] = field(default_factory=lambda: defaultdict(list))
    finals: list[Symbol] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

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
        return chain(self.initials, *self.tree.values())

    def serialize(self) -> dict[str, Any]:
        nodes = [symbol.serialize() for symbol in self.symbols]

        edges = [
            {"from": str(symbol.s_id), "to": str(successor.s_id), "color": "gray"}
            for symbol, successors in self.tree.items()
            for successor in successors
        ]

        return {"nodes": nodes, "edges": edges}

    def copy(self):
        return SymbolGraph(
            initials=self.initials.copy(),
            tree=self.tree.copy(),
            finals=self.finals.copy(),
            metadata=self.metadata.copy(),
        )
