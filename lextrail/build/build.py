from typing import Deque

from lextrail.base import OrderedSet, Symbol, SymbolGraph, SymbolGraphType, SymbolType
from lextrail.build.passes import (
    _build_symbol_from_string,
    _convert_str_def_to_str_queue,
    _get_once_initial_end_def_symbols,
)
from lextrail.helpers import (
    _discard_single_nodes_from_tree,
    _fetch_end_def_symbol_in_sequence,
    _fetch_symbol_predecessors_in_tree,
    _is_end_def_symbol,
    _is_end_def_symbol_in_sequence,
)


def construct_symbol_subgraph(
    symbols_str: list[str], graph_type: SymbolGraphType = SymbolGraphType.STANDARD
) -> SymbolGraph:
    symbol_graph = SymbolGraph()

    # Empty symbol graph.
    if len(symbols_str) == 0:
        return symbol_graph

    # INITIALS
    initial = _build_symbol_from_string(symbols_str[0])
    # Add the node to the initials.
    symbol_graph.initials.add(initial)
    # Add the node to the symbol graph.
    symbol_graph.tree[initial]

    # Single node.
    if len(symbols_str) == 1:
        symbol_graph.initials, symbol_graph.finals = OrderedSet([initial]), OrderedSet(
            [initial]
        )
        # Node without connections.
        symbol_graph.tree[initial]
        return symbol_graph

    symbol_previous = initial
    for symbol_str in symbols_str[1:]:
        if symbol_str == "|":
            symbol_graph.finals.add(symbol_previous)
            continue

        node = _build_symbol_from_string(symbol_str)

        if symbol_previous in symbol_graph.finals:
            # Add the node to the initials.
            symbol_graph.initials.add(node)
            # Add the node to the symbol graph.
            symbol_graph.tree[node]
            symbol_previous = node
            continue

        symbol_graph.tree[symbol_previous].add(node)

        symbol_previous = node

    # FINALS
    # Add the node to the finals.
    symbol_graph.finals.add(symbol_previous)

    return cast_symbol_graph(symbol_graph, graph_type)


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

    # Passing by value and not by reference, avoids modifying the original dicts.
    symbol_graph_lhs_copy = symbol_graph_lhs.copy()
    symbol_graph_rhs_copy = symbol_graph_rhs.copy()

    # Keeps the initials from the left symbol graph and the finals from the right symbol graph.
    symbol_graph_initials_out = symbol_graph_lhs_copy.initials
    symbol_graph_finals_out = symbol_graph_rhs_copy.finals

    # Single node symbols will connect through their `INITIALS` and `FINALS`.
    symbol_graph_lhs_copy.tree = _discard_single_nodes_from_tree(
        symbol_graph_lhs_copy.tree
    )
    symbol_graph_rhs_copy.tree = _discard_single_nodes_from_tree(
        symbol_graph_rhs_copy.tree
    )

    # Union the connections between both symbol graphs.
    symbol_graph_tree_out = symbol_graph_lhs_copy.tree | symbol_graph_rhs_copy.tree

    # Allow skipping rule, search for `END_DEF` symbols that are not finals but were once initials
    # for "NONE_ANY" and "NONE_ONCE" symbol graphs.
    # [TODO] Could construct one list that contains all "END_DEF" symbols, it'll remove the need
    # to go through the `symbol_graph_lhs_copy.finals` below. Keep modularity and separation
    # between both "END_DEF" symbols for the moment.
    # [NOTE] `single_symbols` are symbols without a connection.

    (
        once_end_def_symbols_in_tree,
        once_end_def_symbols_in_initials,
    ) = _get_once_initial_end_def_symbols(symbol_graph_lhs_copy)

    assert len(once_end_def_symbols_in_initials) in [
        0,
        1,
    ], "Repeated `END_DEF` symbol in initials."
    if len(once_end_def_symbols_in_initials) == 1:
        symbol_graph_lhs_copy.initials.discard(once_end_def_symbols_in_initials[0])
        symbol_graph_lhs_copy.initials.extend(symbol_graph_rhs_copy.initials)

    # Connect the left `FINALS` (also takes care of `END_DEF`s) with the right `INITIALS`.
    for symbol_final in (
        list(symbol_graph_lhs_copy.finals) + once_end_def_symbols_in_tree
    ):
        if _is_end_def_symbol(symbol_final):
            symbol_predecessors = _fetch_symbol_predecessors_in_tree(
                symbol_graph_tree_out, symbol_final
            )

            # Discarding the connection to `END_DEF` symbol.
            for symbol_predecessor in symbol_predecessors:
                symbol_graph_tree_out[symbol_predecessor].discard(symbol_final)
            symbol_final = symbol_predecessors

        if not isinstance(symbol_final, list):
            symbol_final = [symbol_final]

        for symbol_initial in symbol_graph_rhs_copy.initials:
            for final in symbol_final:
                symbol_graph_tree_out[final].add(symbol_initial)

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

    # Passing by value and not by reference, avoids modifying the original dicts.
    symbol_graph_lhs_copy = symbol_graph_lhs.copy()
    symbol_graph_rhs_copy = symbol_graph_rhs.copy()

    # Extend the left `INITIALS` to the right `INITIALS`, `|` is not used because it discards the order (*for testing).

    # Removes duplicates (if they exist) `END_DEF` symbols from `INITIALS`.
    if _is_end_def_symbol_in_sequence(
        symbol_graph_lhs_copy.initials
    ) and _is_end_def_symbol_in_sequence(symbol_graph_rhs_copy.initials):
        symbol_special_eos_symbol = _fetch_end_def_symbol_in_sequence(
            symbol_graph_rhs_copy.initials
        )
        symbol_graph_rhs_copy.initials.discard(symbol_special_eos_symbol[0])

    symbol_graph_initials_out = symbol_graph_lhs_copy.initials.extend(
        symbol_graph_rhs_copy.initials
    )

    # Union two `symbol_graphs`, both without their `INITIALS` and `FINALS`.
    symbol_graph_tree_out = symbol_graph_lhs_copy.tree | symbol_graph_rhs_copy.tree

    # Extend the left `FINALS` to the right `FINALS`, `|` is not used because it discards the order (*for testing).
    symbol_graph_finals_out = symbol_graph_lhs_copy.finals.extend(
        symbol_graph_rhs_copy.finals
    )

    return SymbolGraph(
        initials=symbol_graph_initials_out,
        tree=symbol_graph_tree_out,
        finals=symbol_graph_finals_out,
    )


def cast_symbol_graph(
    symbol_graph: SymbolGraph,
    cast_type: SymbolGraphType,
) -> SymbolGraph:
    symbol_graph_copy = symbol_graph.copy()

    if cast_type == SymbolGraphType.NONE_ANY:
        # Add a `END_DEF` to the `initials`, since it can be `NONE`.
        # Add a loop since it's a `(A..Z)*` expression, last element `Z` should connect to the first element `A`.
        # Should add a `END_DEF` to `A` and `Z` (symbols should be different) if `Z` is not connected to any node (always add it, if it's connected to some node remove it afterwards while connecting the graphs)
        # How?
        # During connection, we'll have `END_DEF` -> `Node` -> replace `END_DEF` with the predecessor of `END_DEF`, disconnect predecessor from 'END_DEF`.
        # Each node has a unique identifier, so we'll always be able to track the right predecessor.

        for symbol_final in symbol_graph_copy.finals:
            if symbol_final.content == "END_DEF":
                # [PERFORMANCE] Could raise a flag here and avoid calling is_contain_EOS(symbol_graph_copy.finals) below.
                symbol_predecessors = _fetch_symbol_predecessors_in_tree(
                    symbol_graph_copy.tree, symbol_final
                )

                # Removing the `END_DEF` node.
                # [NOTE] It shouldn't be removed, it'll be used as `END_DEF` node
                # for the casted graph keeping single `END_DEF` nodes.
                # del symbol_graph_copy[symbol_final]

                # Removing the connection of the predecessor with `END_DEF`.
                # [NOTE] It shouldn't be removed, you still want to access `END_DEF` from the subgraph.
                # symbol_graph_copy.tree[symbol_predecessor].discard(symbol_final)
                symbol_final = symbol_predecessors

            if not isinstance(symbol_final, list):
                symbol_final = [symbol_final]

            # Connecting the FINALS with the INITIALS.
            for symbol_initial in symbol_graph_copy.initials:
                if symbol_initial.content == "END_DEF":
                    continue
                for final in symbol_final:
                    symbol_graph_copy.tree[final].add(symbol_initial)

        if _is_end_def_symbol_in_sequence(
            symbol_graph_copy.initials
        ) and _is_end_def_symbol_in_sequence(symbol_graph_copy.finals):
            return symbol_graph_copy

        if not _is_end_def_symbol_in_sequence(symbol_graph_copy.initials):
            # `END_DEF` symbol for the initials.
            symbol_special_eos_initial = Symbol("END_DEF", SymbolType.SPECIAL)

            # Add `END_DEF` as `initials`.
            symbol_graph_copy.initials.add(symbol_special_eos_initial)

            # Add `END_DEF` as node.
            symbol_graph_copy.tree[symbol_special_eos_initial]

        if not _is_end_def_symbol_in_sequence(symbol_graph_copy.finals):
            # `END_DEF` symbols for the initials and finals.
            symbol_special_eos_final = Symbol("END_DEF", SymbolType.SPECIAL)

            # Connect the `END_DEF` in `FINALS` with the elements in the "previous" (before cast) `FINALS`.
            for symbol_final in symbol_graph_copy.finals:
                symbol_graph_copy.tree[symbol_final].add(symbol_special_eos_final)

            # Clear the finals since the `END_DEF` will be the only element in the finals.
            symbol_graph_copy.finals = OrderedSet([])

            # Add `END_DEF` as `finals`.
            symbol_graph_copy.finals.add(symbol_special_eos_final)

        return symbol_graph_copy

    elif cast_type == SymbolGraphType.ONCE_ANY:
        # Same approach as `NONE_ANY`.
        for symbol_final in symbol_graph_copy.finals:
            if symbol_final.content == "END_DEF":
                symbol_predecessors = _fetch_symbol_predecessors_in_tree(
                    symbol_graph_copy.tree, symbol_final
                )

                symbol_final = symbol_predecessors

            if not isinstance(symbol_final, list):
                symbol_final = [symbol_final]

            # Connecting the FINALS with the INITIALS.
            for symbol_initial in symbol_graph_copy.initials:
                if symbol_initial.content == "END_DEF":
                    continue
                for final in symbol_final:
                    symbol_graph_copy.tree[final].add(symbol_initial)

        # Difference lies in not having an `END_DEF` as an initial.
        if not _is_end_def_symbol_in_sequence(
            symbol_graph_copy.initials
        ) and _is_end_def_symbol_in_sequence(symbol_graph_copy.finals):
            return symbol_graph_copy

        if _is_end_def_symbol_in_sequence(symbol_graph_copy.initials):
            # Search for `END_DEF` symbol in the initials.
            initial_end_def_symbols = _fetch_end_def_symbol_in_sequence(
                symbol_graph_copy.initials
            )

            # The logic would (normally) not duplicate `END_DEF` symbols in the initials
            # or the finals.
            assert (
                len(initial_end_def_symbols) == 1
            ), "Initials should contain one `END_DEF` symbol"

            # Discard the `END_DEF` symbol from the initials.
            symbol_graph_copy.initials.discard(initial_end_def_symbols[0])

            # Discard the `END_DEF` symbol from the tree.
            del symbol_graph_copy.tree[initial_end_def_symbols[0]]

        # Same as `NONE_ANY`.
        if not _is_end_def_symbol_in_sequence(symbol_graph_copy.finals):
            # `END_DEF` symbols for the initials and finals.
            symbol_special_eos_final = Symbol("END_DEF", SymbolType.SPECIAL)

            # Connect the `END_DEF` in `FINALS` with the elements in the "previous" (before cast) `FINALS`.
            for symbol_final in symbol_graph_copy.finals:
                symbol_graph_copy.tree[symbol_final].add(symbol_special_eos_final)

            # Clear the finals since the `END_DEF` will be the only element in the finals.
            symbol_graph_copy.finals = OrderedSet([])

            # Add `END_DEF` as `finals`.
            symbol_graph_copy.finals.add(symbol_special_eos_final)

        return symbol_graph_copy

    elif cast_type == SymbolGraphType.NONE_ONCE:
        # Add a `END_DEF` to the SOURCE, since it can be `NONE`.

        # Check if `END_DEF` already exists.
        for symbol_initial in symbol_graph_copy.initials:
            if symbol_initial.content == "END_DEF":
                return symbol_graph_copy

        # Add `END_DEF` as `initials`.
        symbol_special_eos_initial = Symbol("END_DEF", SymbolType.SPECIAL)
        symbol_graph_copy.initials.add(symbol_special_eos_initial)
        symbol_graph_copy.tree[symbol_special_eos_initial]
        return symbol_graph_copy

    else:
        if _is_end_def_symbol_in_sequence(
            symbol_graph_copy.initials
        ) and _is_end_def_symbol_in_sequence(symbol_graph_copy.finals):
            return symbol_graph_copy
        return symbol_graph_copy


def build_symbol_graph(symbol_def: str) -> SymbolGraph:
    queue_symbol_def = _convert_str_def_to_str_queue(symbol_def)

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
    def recurse_build(queue_symbol_def: Deque[str]):
        current_stack_accumulated_symbols: list[str] = []
        current_stack_accumulated_symbol_graph: SymbolGraph = SymbolGraph()
        while True:
            str_symbol = queue_symbol_def.popleft()

            if str_symbol in ("(", "[", "<", "{"):
                symbol_graph_bottom_level = construct_symbol_subgraph(
                    current_stack_accumulated_symbols
                )

                # What happens if `current_stack_accumulated_symbols` is not cleared?
                # Let's have a look at the following example: (_1 `def_1` (_2 `def_2` 2_) `def_3` ) 1_)
                # Each (_NUM should be looked at as a stack,
                # Since we're building accordingly from the left, what'll happen is upon leaving the second
                # stack, we would have already built and connected `def_1` and `def_2`.
                # Then while consuming the symbols `def_3`, we'll have additional symbols from `def_1`.
                current_stack_accumulated_symbols.clear()

                symbol_graph_upper_level = recurse_build(queue_symbol_def)

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
                            current_stack_accumulated_symbols[:index]
                        ),
                        construct_symbol_subgraph(
                            current_stack_accumulated_symbols[index + 1 :]
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
                    current_stack_accumulated_symbols
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
                    current_stack_accumulated_symbols
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

                from_upper_stack_to_accumulate_symbol_graph = recurse_build(
                    queue_symbol_def
                )

                current_stack_accumulated_symbol_graph = union_symbol_graph(
                    current_stack_accumulated_symbol_graph,
                    from_upper_stack_to_accumulate_symbol_graph,
                )

                if bool(queue_symbol_def):
                    continue

                return current_stack_accumulated_symbol_graph

            current_stack_accumulated_symbols.append(str_symbol)

    return recurse_build(queue_symbol_def)
