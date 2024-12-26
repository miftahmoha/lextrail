from typing import Deque, Optional

import matplotlib.axes
import matplotlib.pyplot as plt
import networkx as nx

from lextrail.base import CFGStatefulGraph, Symbol, SymbolGraph, SymbolType
from lextrail.helpers import _is_end_def_symbol

from lextrail.helpers import _get_symbols_from_generated_symbol_graph


def _setup_symbol_graph_networkx(
    symbol_graph: SymbolGraph,
    highlight: Optional[Symbol] = None,
    ax: Optional[matplotlib.axes.Axes] = None,
    display_headers: bool = False,
):
    G = nx.DiGraph()

    # Passing by value, not by reference.
    symbol_graph_copy = symbol_graph.copy()

    symbols = _get_symbols_from_generated_symbol_graph(symbol_graph_copy)

    if display_headers:
        # Adding initials and finals as `Symbols` for visual purposes.
        symbol_special_initials, symbol_special_finals = Symbol(
            "INITIALS", SymbolType.SPECIAL
        ), Symbol("FINALS", SymbolType.SPECIAL)
        symbols["INITIALS"], symbols["FINALS"] = (
            symbol_special_initials,
            symbol_special_finals,
        )

        # Adding the connections.
        (
            symbol_graph_copy.tree[symbol_special_initials],
            symbol_graph_copy.tree[symbol_special_finals],
        ) = (symbol_graph_copy.initials, symbol_graph_copy.finals)

    labels = {}

    for symbol in symbols.values():
        G.add_node(symbol)
        labels[symbol] = symbol.content

    for symbol, connections in symbol_graph_copy.tree.items():
        for connection in connections:
            G.add_edge(symbol, connection)

    # Setting the layout.
    pos = nx.nx_agraph.graphviz_layout(G, prog="dot")

    # Setting a highlight.
    if highlight is None:
        node_color = ["lightblue" for symbol in symbols.values()]
    elif highlight.s_type == SymbolType.NON_TERMINAL:
        node_color = [
            "red" if (symbol == highlight) else "lightblue"
            for symbol in symbols.values()
        ]
    elif (
        highlight.s_type == SymbolType.TERMINAL
        or highlight.s_type == SymbolType.REGEX
        or _is_end_def_symbol(highlight)
    ):
        node_color = [
            "orange" if (symbol == highlight) else "lightblue"
            for symbol in symbols.values()
        ]

    # Using graphviz to layout the tree.
    nx.draw(
        G,
        pos,
        with_labels=True,
        labels=labels,
        node_size=800,
        node_color=node_color,  # type: ignore
        edgecolors="gray",
        alpha=0.8,
        edge_color="gray",
        font_size=12,
        font_family="monospace",
        ax=ax,
    )


def draw_symbol_graph(symbol_graph: SymbolGraph):
    _setup_symbol_graph_networkx(symbol_graph)
    plt.show()


def draw_cfg_generation_state(cfg_generation_state: Deque[CFGStatefulGraph]):
    num_plots = len(cfg_generation_state)

    _, axes = plt.subplots(1, num_plots, figsize=(15, 10))

    for i, cfg_stateful_graph in enumerate(cfg_generation_state):
        _setup_symbol_graph_networkx(
            cfg_stateful_graph.graph, cfg_stateful_graph.state, axes[i]
        )
        axes[i].set_title(f"[Lv.{i}] {cfg_stateful_graph.label}")

    plt.tight_layout()
    plt.show()
