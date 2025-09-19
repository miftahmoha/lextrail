import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from itertools import chain
from typing import Any, Generic, Optional, TypeVar

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
    s_type: "SymbolType" = SymbolType.NONE
    s_id: uuid.UUID = field(default_factory=lambda: uuid.uuid4())
    s_metadata: dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.s_id)

    def __eq__(self, other):
        # Ensure equality is checked for all fields.
        if not isinstance(other, Symbol):
            return False

        return (
            (self.content == other.content)
            and (self.s_type == other.s_type)
            and (self.s_id == other.s_id)
        )

    # def __bool__(self):
    #     # [TODO] Check if empty lexems are not allowed, it not, then `SymbolType.NONE` is not needed.
    #     return self.content and self.s_type == SymbolType.NONE

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


@dataclass(slots=True)
class CFGStatefulGraph:
    graph: SymbolGraph
    label: str
    state: Optional[Symbol] = None

    def __bool__(self) -> bool:
        return bool(self.graph) and bool(self.label) and bool(self.state)

    def __hash__(self):
        return hash((self.label, self.state))

    def __eq__(self, other):
        return (
            (self.graph == other.graph)
            and (self.label == other.label)
            and (self.state == other.state)
        )

    def serialize(self):
        return {
            "graph": self.graph.serialize(),
            "state": self.state.serialize(),
            "label": self.label,
        }

    def copy(self):
        return CFGStatefulGraph(
            graph=self.graph.copy(), label=self.label, state=self.state
        )


class LTDeque(deque, Generic[T]):
    def copy(self) -> "LTDeque[T]":
        return LTDeque(state.copy() for state in self)

    # Ensure other methods (like slicing) also use this behavior.
    def __copy__(self) -> "LTDeque[T]":
        return self.copy()

    def serialize(self):
        return [stateful_graph.serialize() for stateful_graph in self]


CFGGenerationState = LTDeque[CFGStatefulGraph]
