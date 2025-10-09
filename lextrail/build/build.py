from typing import Any, Deque, Dict, List

from lextrail.base import Symbol, SymbolGraph, SymbolGraphType, SymbolType
from lextrail.build.passes import build_symbol_from_lexeme, definition_into_lexeme_queue
from lextrail.exceptions import BuildError
from lextrail.helpers import (
    contains_end_def_symbol,
    get_end_def_symbols,
    get_symbol_predecessors,
    is_end_def_symbol,
    remove_single_nodes,
)


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

    symbol_graph_initials_out, symbol_graph_finals_out = (
        symbol_graph_lhs.initials,
        symbol_graph_rhs.finals,
    )

    # Single node symbols will connect through the `initials` and `finals` attributes.
    symbol_graph_lhs.tree = remove_single_nodes(symbol_graph_lhs.tree)
    symbol_graph_rhs.tree = remove_single_nodes(symbol_graph_rhs.tree)

    symbol_graph_tree_out = symbol_graph_lhs.tree | symbol_graph_rhs.tree

    # Allow skipping rule, search for `END_DEF` symbols that are not finals but were once initials
    # for "NONE_ANY" and "NONE_ONCE" symbol graphs.
    # [TODO] Could construct one list that contains all "END_DEF" symbols, it'll remove the need
    # to go through the `symbol_graph_lhs_copy.finals` below. Keep modularity and separation
    # between both "END_DEF" symbols for the moment.
    once_end_def_symbols_in_initials = [
        symbol for symbol in symbol_graph_lhs.initials if is_end_def_symbol(symbol)
    ]

    assert len(once_end_def_symbols_in_initials) in [
        0,
        1,
    ], "Duplicate `END_DEF` symbol in initials."

    if len(once_end_def_symbols_in_initials) == 1:
        symbol_graph_lhs.initials.remove(once_end_def_symbols_in_initials[0])
        symbol_graph_lhs.initials.extend(symbol_graph_rhs.initials)

    for symbol_final in symbol_graph_lhs.finals:
        symbol_predecessors = []

        if is_end_def_symbol(symbol_final):
            symbol_predecessors = get_symbol_predecessors(
                symbol_graph_tree_out, symbol_final
            )

            for symbol_predecessor in symbol_predecessors:
                symbol_graph_tree_out[symbol_predecessor].remove(symbol_final)

        symbol_finals = symbol_predecessors if symbol_predecessors else [symbol_final]

        for symbol_final_ in symbol_finals:
            for symbol_initial in symbol_graph_rhs.initials:
                # `END_DEF` should always be final symbols, duplication in finals
                # is not an issue when the predecessors are distinct. However, duplicates
                # in initials is an issue, since they have no successors, nor predecessors.
                # [NOTE] Not really, since at some point, we do mutate the predecessors of
                # `END_DEF` symbols to connect to somewhere else. Getting the predecessors
                # the next time will lead to an error. Could be fixed later, a set will
                # eventually be used instead of a list.
                if (
                    is_end_def_symbol(symbol_initial)
                    and symbol_initial not in symbol_graph_finals_out
                ):
                    symbol_graph_finals_out.append(symbol_initial)

                symbol_graph_tree_out[symbol_final_].append(symbol_initial)

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

    # Avoid duplicate `END_DEF` symbols in the initials.
    if contains_end_def_symbol(symbol_graph_lhs.initials) and contains_end_def_symbol(
        symbol_graph_rhs.initials
    ):
        symbol_special_eos_symbols_rhs = get_end_def_symbols(symbol_graph_rhs.initials)
        symbol_graph_rhs.initials.remove(symbol_special_eos_symbols_rhs[0])

    return SymbolGraph(
        initials=symbol_graph_lhs.initials + symbol_graph_rhs.initials,
        tree=symbol_graph_lhs.tree | symbol_graph_rhs.tree,
        finals=symbol_graph_lhs.finals + symbol_graph_rhs.finals,
    )


def cast_symbol_graph(
    symbol_graph: SymbolGraph,
    cast_type: SymbolGraphType,
) -> SymbolGraph:
    if cast_type == SymbolGraphType.NONE_ANY:
        # (1) Add a `END_DEF` to the `initials`, since it can be `NONE`.
        # (2) Add a loop since it's a `(A..Z)*` expression, last element `Z` should connect to the first element `A`.
        # Should add a `END_DEF` to `A` and `Z` (symbols should be different),
        # if `Z` is not connected to any node (always add it, if it's connected to some node remove it afterwards while connecting the graphs)
        # How?
        # During connection, we'll have `END_DEF` -> `Node` -> replace `END_DEF` with the predecessor of `END_DEF`, disconnect predecessor from 'END_DEF`.
        # Each node has a unique identifier, so we'll always be able to track the right predecessor.
        for symbol_final in symbol_graph.finals:
            symbol_predecessors = []
            if is_end_def_symbol(symbol_final):
                symbol_predecessors = get_symbol_predecessors(
                    symbol_graph.tree, symbol_final
                )
            symbol_finals = (
                symbol_predecessors if symbol_predecessors else [symbol_final]
            )
            for symbol_initial in symbol_graph.initials:
                if is_end_def_symbol(symbol_initial):
                    continue
                for symbol_final in symbol_finals:
                    # We should make sure there are no duplicates connections, if the cast
                    # is applied multiple times.
                    if symbol_initial not in symbol_graph.tree[symbol_final]:
                        symbol_graph.tree[symbol_final].append(symbol_initial)

        if contains_end_def_symbol(symbol_graph.initials) and contains_end_def_symbol(
            symbol_graph.finals
        ):
            return symbol_graph

        if not contains_end_def_symbol(symbol_graph.initials):
            symbol_special_eos_initial = Symbol("END_DEF", SymbolType.SPECIAL)
            symbol_graph.initials.append(symbol_special_eos_initial)
            symbol_graph.tree[symbol_special_eos_initial]

        if not contains_end_def_symbol(symbol_graph.finals):
            symbol_special_eos_final = Symbol("END_DEF", SymbolType.SPECIAL)
            for symbol_final in symbol_graph.finals:
                symbol_graph.tree[symbol_final].append(symbol_special_eos_final)
            symbol_graph.tree[symbol_special_eos_final]
            symbol_graph.finals = [symbol_special_eos_final]

        return symbol_graph

    elif cast_type == SymbolGraphType.ONCE_ANY:
        # Same approach as `NONE_ANY`.
        for symbol_final in symbol_graph.finals:
            symbol_predecessors = []
            if is_end_def_symbol(symbol_final):
                symbol_predecessors = get_symbol_predecessors(
                    symbol_graph.tree, symbol_final
                )
            symbol_finals = (
                symbol_predecessors if symbol_predecessors else [symbol_final]
            )
            for symbol_initial in symbol_graph.initials:
                if is_end_def_symbol(symbol_initial):
                    continue
                for symbol_final in symbol_finals:
                    # We should make sure there are no duplicates connections, if the cast
                    # is applied multiple times.
                    if symbol_initial not in symbol_graph.tree[symbol_final]:
                        symbol_graph.tree[symbol_final].append(symbol_initial)

        # Difference resides in not having an `END_DEF` as an initial.
        if not contains_end_def_symbol(
            symbol_graph.initials
        ) and contains_end_def_symbol(symbol_graph.finals):
            return symbol_graph

        if contains_end_def_symbol(symbol_graph.initials):
            initial_end_def_symbols = get_end_def_symbols(symbol_graph.initials)
            assert (
                len(initial_end_def_symbols) == 1
            ), "Initials should contain one `END_DEF` symbol"
            symbol_graph.initials.remove(initial_end_def_symbols[0])
            del symbol_graph.tree[initial_end_def_symbols[0]]

        # Same as `NONE_ANY`.
        if not contains_end_def_symbol(symbol_graph.finals):
            symbol_special_eos_final = Symbol("END_DEF", SymbolType.SPECIAL)
            for symbol_final in symbol_graph.finals:
                symbol_graph.tree[symbol_final].append(symbol_special_eos_final)
            symbol_graph.finals = []
            symbol_graph.finals.append(symbol_special_eos_final)

        return symbol_graph

    elif cast_type == SymbolGraphType.NONE_ONCE:
        for symbol_initial in symbol_graph.initials:
            if is_end_def_symbol(symbol_initial):
                return symbol_graph

        symbol_special_eos_initial = Symbol("END_DEF", SymbolType.SPECIAL)
        symbol_graph.initials.append(symbol_special_eos_initial)
        symbol_graph.tree[symbol_special_eos_initial]
        return symbol_graph

    elif cast_type == SymbolGraphType.STANDARD:
        return symbol_graph

    else:
        raise BuildError(f"Invalid cast {cast_type}.")


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
                    SYMBOL_GRAPH_TYPE = SymbolGraphType.STANDARD
                elif str_symbol == "}":
                    SYMBOL_GRAPH_TYPE = SymbolGraphType.NONE_ANY
                elif str_symbol == ">":
                    SYMBOL_GRAPH_TYPE = SymbolGraphType.ONCE_ANY
                elif str_symbol == "]":
                    SYMBOL_GRAPH_TYPE = SymbolGraphType.NONE_ONCE

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
