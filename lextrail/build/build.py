from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from os import getenv
from typing import Any, Deque, Dict, List

from lextrail.base import Symbol, SymbolGraph, SymbolType
from lextrail.build.passes import build_symbol_from_lexeme, definition_into_lexeme_queue
from lextrail.exceptions import BuildError
from lextrail.helpers import is_end_def_symbol, remove_single_nodes, safe_node_connect


def construct_symbol_subgraph(
    lexems: List[str],
    metadata: Dict[str, Any] = {},
) -> SymbolGraph:
    symbol_graph = SymbolGraph()

    if not lexems:
        return symbol_graph

    initial = build_symbol_from_lexeme(lexems[0])
    symbol_graph.initials.append(initial)
    symbol_graph.tree[initial]

    if len(lexems) == 1:
        symbol_graph.initials, symbol_graph.finals = [initial], [initial]
        symbol_graph.tree[initial]
        # [NOTE] Metadata used for backreferences.
        for symbol in symbol_graph.symbols:
            symbol.s_metadata = metadata
        return symbol_graph

    previous = initial

    for symbol_str in lexems[1:]:
        if symbol_str == "|":
            symbol_graph.finals.append(previous)
            continue

        node = build_symbol_from_lexeme(symbol_str)

        if previous in symbol_graph.finals:
            symbol_graph.initials.append(node)
            symbol_graph.tree[node]
            previous = node
            continue

        symbol_graph.tree[previous].append(node)

        previous = node

    symbol_graph.finals.append(previous)

    # [NOTE] Metadata used for backreferences.
    for symbol in symbol_graph.symbols:
        symbol.s_metadata = metadata

    return symbol_graph


def construct_symbol_graph(lexemes: list[str]):
    symbol_graph = SymbolGraph()

    if not lexemes:
        return symbol_graph

    previous = build_symbol_from_lexeme(lexemes[0])
    symbol_graph.initials = [previous]
    symbol_graph.tree[previous]

    for lexeme in lexemes[1:]:
        next = build_symbol_from_lexeme(lexeme)
        symbol_graph.tree[previous] = [next]
        previous = next

    symbol_graph.finals = [previous]

    return symbol_graph


def connect_symbol_graph(
    symbol_graph_lhs: SymbolGraph,
    symbol_graph_rhs: SymbolGraph,
) -> SymbolGraph:
    if not symbol_graph_lhs.tree and not symbol_graph_rhs.tree:
        return SymbolGraph()

    elif not symbol_graph_lhs.tree:
        return symbol_graph_rhs

    elif not symbol_graph_rhs.tree:
        return symbol_graph_lhs

    symbol_graph_lhs.tree = remove_single_nodes(symbol_graph_lhs.tree)
    symbol_graph_rhs.tree = remove_single_nodes(symbol_graph_rhs.tree)

    symbol_graph_tree_out = symbol_graph_lhs.tree | symbol_graph_rhs.tree

    if int(getenv("SKIP_RULE", 1)):
        end_def_symbols = [
            symbol for symbol in symbol_graph_lhs.finals if is_end_def_symbol(symbol)
        ]

        assert len(end_def_symbols) <= 1, "Duplicate `END` final symbols."

        for end_def_symbol in end_def_symbols:
            predecessors = [
                parent
                for parent, children in symbol_graph_lhs.tree.items()
                if end_def_symbol in children
            ]

            for predecessor in predecessors:
                symbol_graph_lhs.tree[predecessor].remove(end_def_symbol)

            symbol_graph_lhs.finals.remove(end_def_symbol)
            symbol_graph_lhs.finals.extend(predecessors)

        end_def_symbols = [
            symbol for symbol in symbol_graph_lhs.initials if is_end_def_symbol(symbol)
        ]

        assert len(end_def_symbols) <= 1, "Duplicate `END` initial symbols."

        for end_def_symbol in end_def_symbols:
            symbol_graph_lhs.initials.remove(end_def_symbol)
            symbol_graph_lhs.initials += symbol_graph_rhs.initials

    symbol_graph_initials_out, symbol_graph_finals_out = (
        symbol_graph_lhs.initials,
        symbol_graph_rhs.finals,
    )

    for symbol_final in symbol_graph_lhs.finals:
        for symbol_initial in symbol_graph_rhs.initials:
            # [NOTE] Graphs of kind `NONE_ONCE` have their `END_DEF` symbol as initials, if
            # a graph connects them from the left, then the `END_DEF` symbol must be added to the
            # finals.
            # Not only it's a logical implication, but it allows to not lose track of the `END_DEF`
            # symbol for the next connections.
            if (
                is_end_def_symbol(symbol_initial)
                and symbol_initial not in symbol_graph_rhs.finals
            ):
                symbol_graph_rhs.finals.append(symbol_initial)

            safe_node_connect(symbol_graph_tree_out, symbol_final, symbol_initial)

    return SymbolGraph(
        initials=symbol_graph_initials_out,
        tree=symbol_graph_tree_out,
        finals=symbol_graph_finals_out,
    )


def union_symbol_graph(
    symbol_graph_lhs: SymbolGraph,
    symbol_graph_rhs: SymbolGraph,
) -> SymbolGraph:
    if not symbol_graph_lhs.tree and not symbol_graph_rhs.tree:
        return SymbolGraph()

    elif not symbol_graph_lhs.tree:
        return symbol_graph_rhs

    elif not symbol_graph_rhs.tree:
        return symbol_graph_lhs

    symbol_graph_tree_out = symbol_graph_lhs.tree | symbol_graph_rhs.tree

    # Remove duplicate `END` symbols in the initials.
    end_def_symbols_lhs, end_def_symbols_rhs = (
        [symbol for symbol in symbol_graph_lhs.initials if is_end_def_symbol(symbol)],
        [symbol for symbol in symbol_graph_rhs.initials if is_end_def_symbol(symbol)],
    )

    assert (
        len(end_def_symbols_lhs) <= 1 and len(end_def_symbols_rhs) <= 1
    ), f"Duplicate `END` initial symbols {end_def_symbols_lhs} and {end_def_symbols_rhs}."

    if end_def_symbols_lhs and end_def_symbols_rhs:
        symbol_graph_rhs.initials.remove(end_def_symbols_rhs[0])

    # Remove duplicate `END` symbols in the finals.
    end_def_symbols_lhs, end_def_symbols_rhs = (
        [symbol for symbol in symbol_graph_lhs.finals if is_end_def_symbol(symbol)],
        [symbol for symbol in symbol_graph_rhs.finals if is_end_def_symbol(symbol)],
    )

    assert (
        len(end_def_symbols_lhs) <= 1 and len(end_def_symbols_rhs) <= 1
    ), "Duplicate `END` final symbols."

    if end_def_symbols_lhs and end_def_symbols_rhs:
        predecessors = [
            parent
            for parent, children in symbol_graph_rhs.tree.items()
            if end_def_symbols_rhs[0] in children
        ]

        for predecessor in predecessors:
            symbol_graph_tree_out[predecessor].remove(end_def_symbols_rhs[0])
            symbol_graph_tree_out[predecessor].append(end_def_symbols_lhs[0])

        symbol_graph_rhs.finals.remove(end_def_symbols_rhs[0])

    return SymbolGraph(
        initials=symbol_graph_lhs.initials + symbol_graph_rhs.initials,
        tree=symbol_graph_tree_out,
        finals=symbol_graph_lhs.finals + symbol_graph_rhs.finals,
    )


class SymbolGraph_Kind(Enum):
    DEFAULT = 1
    NONE_ANY = 2
    ONCE_ANY = 4
    NONE_ONCE = 3
    OR = 5


def cast_symbol_graph(symbol_graph: SymbolGraph, kind: SymbolGraph_Kind):
    if kind == SymbolGraph_Kind.DEFAULT:
        return symbol_graph

    elif kind == SymbolGraph_Kind.NONE_ANY:
        initials, tree, finals = (
            symbol_graph.initials,
            symbol_graph.tree,
            symbol_graph.finals,
        )

        # [NOTE] Avoids duplicated `END_DEF` symbols that could come from either:
        # (1) NONE_ANY: `END_DEF` would be in both the initials and finals.
        # (2) ONCE_ANY: `END_DEF` would be in the finals.
        # (3) NONE_ONCE: `END_DEF` would be in the initials.
        end_def_symbol = (
            next((s for s in initials if is_end_def_symbol(s)), None)
            or next((s for s in finals if is_end_def_symbol(s)), None)
            or initials.append(Symbol("END_DEF", SymbolType.SPECIAL))  # type: ignore
            or initials[-1]
        )

        # Need to re-establish the loop for mixed graphs built through unions.
        finals += (
            [parent for parent, children in tree.items() if end_def_symbol in children]
            if end_def_symbol in finals
            else []
        )

        for final in finals:
            for initial in initials:
                # Nested casts would lead to duplicates.
                safe_node_connect(tree, final, initial)

        symbol_graph.finals = [end_def_symbol]

        return symbol_graph

    elif kind == SymbolGraph_Kind.NONE_ONCE:
        initials, tree = symbol_graph.initials, symbol_graph.tree

        end_def_symbol = (
            next((s for s in initials if is_end_def_symbol(s)), None)
            or initials.append(Symbol("END_DEF", SymbolType.SPECIAL))  # type: ignore
            or initials[-1]
        )

        tree[end_def_symbol] = []

        return symbol_graph

    elif kind == SymbolGraph_Kind.ONCE_ANY:
        initials, tree, finals = (
            symbol_graph.initials,
            symbol_graph.tree,
            symbol_graph.finals,
        )

        # Avoids duplicated `END_DEF` symbols that could come from either:
        # (1) NONE_ANY: `END_DEF` would be in both the initials and finals.
        # (2) ONCE_ANY: `END_DEF` would be in the finals.
        # (3) NONE_ONCE: `END_DEF` would be in the initials
        end_def_symbol = (
            next((s for s in initials if is_end_def_symbol(s)), None)
            or next((s for s in finals if is_end_def_symbol(s)), None)
            or Symbol("END_DEF", SymbolType.SPECIAL)
        )

        # Need to re-establish the loop for mixed graphs built through unions.
        finals += (
            [parent for parent, children in tree.items() if end_def_symbol in children]
            if end_def_symbol in finals
            else []
        )

        for final in finals:
            for initial in initials:
                # Nested casts would lead to duplicates.
                safe_node_connect(tree, final, initial)

            # Nested casts would lead to duplicates.
            safe_node_connect(tree, final, end_def_symbol)

        symbol_graph.finals = [end_def_symbol]

        return symbol_graph

    else:
        raise BuildError(f"Invalid cast {kind}.")


def build_symbol_graph(
    symbol_def: str, _GLOBAL_COUNT=0, _GLOBAL_COUNT_TO_DEPTH: dict[int, int] = {}
) -> SymbolGraph:
    queue_symbol_def = definition_into_lexeme_queue(symbol_def)

    # We build graphs from the left, (_1 `def_1` (_2 `def_2` 2_) `def_3` (_3 def_4 3_) 1_),
    # Each time, we encounter an opening delimiter `(, [, {`, we build what we accumulated before it.
    # In the example above, there nothing before, thus we're going to build an empty subgraph,
    # let's call it `subgraph_{0}`. `_{}` refers to the stack level.
    # `subgraph_{0}` is stored in a variable called `symbol_graph_bottom_level_{0}`, as you might have guessed,
    # it refers to the bottom stack layer.
    # Because we can look at it as follows:
    # (_0 [EMPTY_GRAPH] --> `symbol_graph_bottom_level_{0}` (_1 `def_1` (_2 `def_2` 2_) `def_3` ) 1_) 0_)
    # When we reach a new stack layer, in the example `(_2`, we'll recurse through the next stack layer `(_2`
    # and return the result (when we encouter a closing delimiter `), ], }`) to a variable called `symbol_graph_upper_level_{1}`.
    # Then we build `def_2` which'll be returned to `symbol_graph_upper_level_{1}`.
    # Finally, it'll be connected to `def_1` and stored into a variable called `symbol_graph_partial_lhs_{1}`.`
    # We repeat the same process within a single stack, we successively build bottom and upper layers,
    # ``def_1` (_2 `def_2` 2_)` and ``def_3` (_3 def_4 3_)` while acummulating the result
    # in `symbol_graph_partial_lhs_{1}` .
    def recurse_build(
        queue_symbol_def: Deque[str],
        queue_symbol_level: int = 0,
        queue_symbol_count: int = 0,
    ):
        current_stack_accumulated_symbols: list[str] = []
        current_stack_accumulated_symbol_graph: SymbolGraph = SymbolGraph()
        nonlocal _GLOBAL_COUNT
        nonlocal _GLOBAL_COUNT_TO_DEPTH
        while True:
            str_symbol = queue_symbol_def.popleft()

            if str_symbol in ("(", "[", "<", "{"):
                symbol_graph_bottom_level = construct_symbol_subgraph(
                    lexems=current_stack_accumulated_symbols,
                    metadata={
                        "_DEPTH": queue_symbol_level,
                        "_COUNT": queue_symbol_count,
                    },
                )

                # What happens if `current_stack_accumulated_symbols` is not cleared?
                # Let's have a look at the following example: (_1 `def_1` (_2 `def_2` 2_) `def_3` ) 1_)
                # Each (_NUM should be looked at as a stack,
                # Since we're building accordingly from the left, what'll happen is upon leaving the second
                # stack, we would have already built and connected `def_1` and `def_2`.
                # Then while consuming the symbols `def_3`, we'll have additional symbols from `def_1`.
                current_stack_accumulated_symbols.clear()

                # Track count for subgraphs.
                _GLOBAL_COUNT += 1

                # Track a mapping from counts to depths for subgraphs.
                _GLOBAL_COUNT_TO_DEPTH[_GLOBAL_COUNT] = queue_symbol_level + 1

                symbol_graph_upper_level = recurse_build(
                    queue_symbol_def,
                    queue_symbol_level + 1,
                    _GLOBAL_COUNT,
                )

                # Accumulates successive bottom-upper stack level symbol graph builds.
                if current_stack_accumulated_symbol_graph:
                    from_upper_stack_to_accumulate_symbol_graph = connect_symbol_graph(
                        symbol_graph_bottom_level, symbol_graph_upper_level
                    )
                    current_stack_accumulated_symbol_graph = connect_symbol_graph(
                        current_stack_accumulated_symbol_graph,
                        from_upper_stack_to_accumulate_symbol_graph,
                    )
                else:
                    current_stack_accumulated_symbol_graph = connect_symbol_graph(
                        symbol_graph_bottom_level, symbol_graph_upper_level
                    )

                # Avoids leaving the the `lower` level stack after terminating a `higher` level stack.
                if bool(queue_symbol_def):
                    continue

                # We need to return at the last delimiter to not pop from an empty queue,
                # the expression needs to be correct syntactically.
                return current_stack_accumulated_symbol_graph

            if str_symbol in (")", "]", ">", "}"):
                if str_symbol == ")":
                    SYMBOL_GRAPH_TYPE = SymbolGraph_Kind.DEFAULT
                elif str_symbol == "}":
                    SYMBOL_GRAPH_TYPE = SymbolGraph_Kind.NONE_ANY
                elif str_symbol == ">":
                    SYMBOL_GRAPH_TYPE = SymbolGraph_Kind.ONCE_ANY
                elif str_symbol == "]":
                    SYMBOL_GRAPH_TYPE = SymbolGraph_Kind.NONE_ONCE

                # Handles the case where there exist no opening `("(", "[", "{")` delimiter next to '|.
                # Example: (_1 `def_1` {_2 `def_2` 2_} `def_4` | `def_3` 1_), with `def_4` which could be empty.
                # In such case, we'll return the union of the left definition (`def_1` {`def_2`} `def_4`) to the `|`
                # with the right definition (`def_3`).
                if "|" in current_stack_accumulated_symbols:
                    index = current_stack_accumulated_symbols.index("|")
                    symbol_graph_or_lhs, symbol_graph_or_rhs = (
                        construct_symbol_subgraph(
                            lexems=current_stack_accumulated_symbols[:index],
                            metadata={
                                "_DEPTH": queue_symbol_level,
                                "_COUNT": queue_symbol_count,
                            },
                        ),
                        construct_symbol_subgraph(
                            lexems=current_stack_accumulated_symbols[index + 1 :],
                            metadata={
                                "_DEPTH": queue_symbol_level,
                                "_COUNT": queue_symbol_count,
                            },
                        ),
                    )
                    # Accumulate the left symbol graph with left portion before the '|' symbol.
                    current_stack_accumulated_symbol_graph = connect_symbol_graph(
                        current_stack_accumulated_symbol_graph, symbol_graph_or_lhs
                    )
                    # Union the left symbol graph with the right portion after the '|' symbol.
                    symbol_graph_out = union_symbol_graph(
                        current_stack_accumulated_symbol_graph, symbol_graph_or_rhs
                    )
                    return cast_symbol_graph(symbol_graph_out, SYMBOL_GRAPH_TYPE)  # type: ignore

                current_stack_to_accumulate_symbol_graph = construct_symbol_subgraph(
                    lexems=current_stack_accumulated_symbols,
                    metadata={
                        "_DEPTH": queue_symbol_level,
                        "_COUNT": queue_symbol_count,
                    },
                )
                symbol_graph_out = connect_symbol_graph(
                    current_stack_accumulated_symbol_graph,
                    current_stack_to_accumulate_symbol_graph,
                )
                return cast_symbol_graph(symbol_graph_out, SYMBOL_GRAPH_TYPE)  # type: ignore

            elif str_symbol == "|":
                # Delegates the case where there exist no opening `("(", "[", "{")`
                # delimiter next to '|' to upper CF.
                if queue_symbol_def[0] not in ["(", "[", "{", "<"]:
                    current_stack_accumulated_symbols.append(str_symbol)
                    continue

                # Handles the case where there exist an opening `("(", "[", "{")` delimiter next to '|.
                # Creates subgraph of accumulated symbols, if they exist; else return an empty graph.
                current_stack_to_accumulate_symbol_graph = construct_symbol_subgraph(
                    lexems=current_stack_accumulated_symbols,
                    metadata={
                        "_DEPTH": queue_symbol_level,
                        "_COUNT": queue_symbol_count,
                    },
                )

                # Consumes `current_stack_accumulated_symbols.`
                current_stack_accumulated_symbols.clear()

                # Accumulates `current_stack_accumulated_symbol_graph`.
                current_stack_accumulated_symbol_graph = connect_symbol_graph(
                    current_stack_accumulated_symbol_graph,
                    current_stack_to_accumulate_symbol_graph,
                )

                # Avoids opening an additional stack.
                # One when encountering the symbol `|` and second with an opening delimiter (`(`, `[`, `{`).
                # Not doing so will (steal) an enclosing delimiter, thus breaking the logic.
                if queue_symbol_def[0] in ["(", "[", "{", "<"]:
                    queue_symbol_def.popleft()

                # Track count for subgraphs.
                _GLOBAL_COUNT += 1

                # Track a mapping from counts to depths for subgraphs.
                _GLOBAL_COUNT_TO_DEPTH[_GLOBAL_COUNT] = queue_symbol_level + 1

                from_upper_stack_to_accumulate_symbol_graph = recurse_build(
                    queue_symbol_def,
                    queue_symbol_level + 1,
                    _GLOBAL_COUNT,
                )

                current_stack_accumulated_symbol_graph = union_symbol_graph(
                    current_stack_accumulated_symbol_graph,
                    from_upper_stack_to_accumulate_symbol_graph,
                )

                if bool(queue_symbol_def):
                    continue

                return current_stack_accumulated_symbol_graph

            current_stack_accumulated_symbols.append(str_symbol)

    symbol_graph = recurse_build(queue_symbol_def)

    # Set global metadata.
    symbol_graph.metadata["_COUNT_TO_DEPTH"] = _GLOBAL_COUNT_TO_DEPTH.copy()

    return symbol_graph


@dataclass(slots=True)
class Accumulator:
    graph: SymbolGraph = field(default_factory=lambda: SymbolGraph())
    kind: SymbolGraph_Kind = SymbolGraph_Kind.DEFAULT


def build_symbol_graph_New(symbol_def: str):
    LEXEME_TO_KIND = {
        "(": SymbolGraph_Kind.DEFAULT,
        "{": SymbolGraph_Kind.NONE_ANY,
        "[": SymbolGraph_Kind.NONE_ONCE,
        "<": SymbolGraph_Kind.ONCE_ANY,
        "|": SymbolGraph_Kind.OR,
    }

    lexemes = definition_into_lexeme_queue(symbol_def)
    state: Deque[Accumulator] = deque([Accumulator()])
    current_accumulated_lexemes: list[str] = []

    while lexemes:
        lexeme = lexemes.popleft()

        if lexeme in "([{<|":
            accumulated_graph = construct_symbol_graph(current_accumulated_lexemes)
            state[-1].graph = connect_symbol_graph(state[-1].graph, accumulated_graph)
            current_accumulated_lexemes.clear()

            state.append(Accumulator(SymbolGraph(), LEXEME_TO_KIND[lexeme]))

        elif lexeme in ")]}>":
            accumulated_graph = construct_symbol_graph(current_accumulated_lexemes)
            state[-1].graph = connect_symbol_graph(state[-1].graph, accumulated_graph)
            current_accumulated_lexemes.clear()

            consumer = state.pop()
            while consumer.kind == SymbolGraph_Kind.OR:
                state[-1].graph = union_symbol_graph(state[-1].graph, consumer.graph)
                consumer = state.pop()

            state[-1].graph = connect_symbol_graph(
                state[-1].graph,
                cast_symbol_graph(consumer.graph, consumer.kind),
            )

        else:
            current_accumulated_lexemes.append(lexeme)

    assert len(state) == 1, "Only one consumer should remain."

    return state.pop().graph
