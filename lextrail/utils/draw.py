from typing import Deque, Optional

import matplotlib.axes
import matplotlib.pyplot as plt
import networkx as nx

from lextrail.base import CFGStatefulGraph, Symbol, SymbolGraph, SymbolType
from lextrail.helpers import (
    _get_symbols_from_generated_symbol_graph,
    _is_end_def_symbol,
)

colors = {"default": "lightblue", "modern_red": "#FF6B6B", "golden_orange": "#FFD166"}


def _setup_symbol_graph_networkx(
    symbol_graph: SymbolGraph,
    highlights: list[Optional[Symbol]] = [],
    ax: Optional[matplotlib.axes.Axes] = None,
    size: int = 800,
):
    if isinstance(highlights, Symbol):
        highlights = [highlights]

    G = nx.DiGraph()

    # Passing by value, not by reference.
    symbol_graph_copy = symbol_graph.copy()

    symbols = _get_symbols_from_generated_symbol_graph(symbol_graph_copy)

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
    pos = nx.nx_agraph.graphviz_layout(G, prog="neato")

    # Setting a highlight.
    if not highlights:
        node_color = [colors["default"] for _ in symbols.values()]
    else:
        node_color = [
            (
                colors["modern_red"]
                if (symbol in highlights and symbol.s_type == SymbolType.NON_TERMINAL)
                else (
                    colors["golden_orange"]
                    if (
                        symbol in highlights
                        and (
                            symbol.s_type == SymbolType.TERMINAL
                            or symbol.s_type == SymbolType.REGEX
                            or _is_end_def_symbol(symbol)
                        )
                    )
                    else colors["default"]
                )
            )
            for symbol in symbols.values()
        ]

    # Using graphviz to layout the tree.
    nx.draw(
        G,
        pos,
        with_labels=True,
        labels=labels,
        node_size=size,
        node_color=node_color,  # type: ignore
        edgecolors="gray",
        alpha=0.85,
        edge_color="gray",
        font_size=12,
        font_family="sans-serif",
        ax=ax,
        connectionstyle="arc3, rad=0.1",
    )


def draw_symbol_graph(symbol_graph: SymbolGraph):
    _setup_symbol_graph_networkx(symbol_graph)
    plt.show()


def draw_cfg_generation_state(cfg_generation_state: Deque[CFGStatefulGraph]):
    num_plots = len(cfg_generation_state)

    _, axes = plt.subplots(1, num_plots, figsize=(15, 10))

    for i, cfg_stateful_graph in enumerate(cfg_generation_state):
        _setup_symbol_graph_networkx(
            cfg_stateful_graph.graph, [cfg_stateful_graph.state], axes[i]
        )
        axes[i].set_title(f"[Lv.{i}] {cfg_stateful_graph.label}")

    plt.tight_layout()
    plt.show()
