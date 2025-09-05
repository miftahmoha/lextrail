import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generic, Iterable, Iterator, Optional, TypeVar
from copy import deepcopy

# [TODO] Will remove the repetition.
def bfs(symbol_graph: "SymbolGraph", start) -> list["Symbol"]:
    visited = []

    queue = deque()  # type: ignore
    queue.extend(list(start))

    while queue:
        vertex = queue.popleft()
        if vertex not in visited:
            visited.append(vertex)
            queue.extend(symbol_graph.tree[vertex])

    return visited

def _get_symbols_from_generated_symbol_graph(
    symbol_graph: "SymbolGraph",
) -> dict[str, "Symbol"]:
    symbols: dict[str, Symbol] = {}

    start = symbol_graph.initials
    visited = bfs(symbol_graph.copy(), start)

    # The default int is set to 0.
    order: dict[str, int] = defaultdict(int)
    for symbol in visited:
        symbols[symbol.content + f"|{order[symbol.content]}"] = symbol
        order[symbol.content] += 1

    return symbols


T = TypeVar("T")

# [TODO] Inspect the need of an ordered set.
class OrderedSet(Generic[T]):
    def __init__(self, iterable: Iterable[T] = None):  # type: ignore
        self._dict: dict[T, None] = dict.fromkeys(iterable if iterable else [])

    def add(self, item: T) -> None:
        self._dict[item] = None

    def discard(self, item: T) -> None:
        if item in self._dict:
            self._dict.pop(item)

    def extend(self, other) -> "OrderedSet[T]":
        for symbol in other:
            self.add(symbol)
        return self

    def __bool__(self) -> bool:
        return bool(self._dict)

    def __contains__(self, item: T) -> bool:
        return item in self._dict

    def __iter__(self) -> Iterator[T]:
        return iter(self._dict.keys())

    def __len__(self) -> int:
        return len(self._dict)

    def __repr__(self) -> str:
        return f"OrderedSet({list(self._dict.keys())})"

    def __eq__(self, other) -> bool:
        if isinstance(other, OrderedSet):
            return list(self) == list(other)  # type: ignore
        return NotImplemented

    def __or__(self, other: "OrderedSet[T]") -> "OrderedSet[T]":
        return OrderedSet(self._dict.keys() | other._dict.keys())

    def __and__(self, other: "OrderedSet[T]") -> "OrderedSet[T]":
        return OrderedSet(self._dict.keys() & other._dict.keys())

    def copy(self) -> "OrderedSet[T]":
        # [NOTE] At some point, using deepcopy wasn't needed until metadata being set
        # of a symbol A was shared with another symbol B within `Guide` at 
        # '"start" "ambiguous" "ambiguous"* "end"' where "ambiguous"(*) shared the metadata with "end".
        # [TODO] Explore the root of the shallow copying in this case.
        return OrderedSet(deepcopy(self._dict))



@dataclass
class Symbol:
    content: str
    s_type: "SymbolType"
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
    
    def serialize(self):
        return {
                # `label` is the convention used by Viz.
                "label": self.content,
                "id": str(self.s_id),
                "type": str(self.s_type),
                }


class SymbolType(Enum):
    TERMINAL = 1
    NON_TERMINAL = 2
    REGEX = 3
    SPECIAL = 4
    REFERENCE = 5


@dataclass(slots=True)
class SymbolGraph:
    initials: OrderedSet[Symbol] = field(default_factory=OrderedSet)
    tree: dict[Symbol, OrderedSet[Symbol]] = field(
        default_factory=lambda: defaultdict(OrderedSet)
    )
    finals: OrderedSet[Symbol] = field(default_factory=OrderedSet)
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
    
    # [TODO] Make it more concise.
    def serialize(self) -> str:
        nodes: list[dict[str, str]] = []
        edges: list[dict[str, str]] = []

        symbols = _get_symbols_from_generated_symbol_graph(self)
        for symbol in symbols.values():
            nodes.append(symbol.serialize())

        for symbol, successors in self.tree.items():
            src_id = str(symbol.s_id)
            for successor in successors:
                dst_id = str(successor.s_id)
                edges.append({"from": src_id, "to": dst_id, "color": "gray"})

        return {"nodes": nodes, "edges": edges}

    # [NOTE] Why is broadcasting needed?
    def broadcast(self, metadata: dict[str, Any]):
        for symbol in self.initials:
            symbol.s_metadata = metadata

        for successors in self.tree.values():
            for symbol in successors:
                symbol.s_metadata = metadata

    def copy(self):
        return SymbolGraph(
            initials=self.initials.copy(),
            tree=self.tree.copy(),
            finals=self.finals.copy(),
            metadata=self.metadata.copy(),
        )


class SymbolGraphType(Enum):
    STANDARD = 1
    NONE_ANY = 2
    ONCE_ANY = 3
    NONE_ONCE = 4


@dataclass
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
        return {"graph": self.graph.serialize(), "state": self.state.serialize(), "label": self.label}

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
