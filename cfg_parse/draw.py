from dataclasses import dataclass, field
from typing import Deque, Optional

import exrex
import matplotlib.axes
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import TextBox

from cfg_parse.base import CFGStatefulGraph, Symbol, SymbolGraph, SymbolType
from cfg_parse.cfg_build.helpers import _get_symbols_from_generated_symbol_graph
from cfg_parse.cfg_guide.guide import CFGGenerationState, CFGGuide
from cfg_parse.cfg_guide.helpers import (
    _get_next_terminal_symbols_as_regex,
    _retrace_symbol_obj_from_str,
)


def _setup_symbol_graph_networkx(
    symbol_graph: SymbolGraph,
    highlight: Optional[Symbol] = None,
    ax: Optional[matplotlib.axes.Axes] = None,
):
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
        highlight.s_type == SymbolType.TERMINAL or highlight.s_type == SymbolType.REGEX
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
        node_color=node_color,
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


@dataclass
class _MockLLM:
    response: str = field(default="")

    # Use `exrex` to generate a sample from a REGEX expression.
    def get_choice(self, regex_str: str) -> str:
        choice = exrex.getone(regex_str)
        if choice == "EOS_SYMBOL":
            return choice
        self.response += choice[1:-1]
        return choice


def _animate_get_guided_response(
    cfg_guide_obj: CFGGuide, chosen_symbol, chosen_symbol_hist, mock_llm: "_MockLLM"
) -> tuple[Optional[Symbol], CFGGenerationState]:
    cfg_guide_obj.get_next_terminals(chosen_symbol_hist, chosen_symbol)
    next_terminals_w_hist = cfg_guide_obj.next_terminals_w_history

    # End generation.
    if not next_terminals_w_hist:
        return None, None

    next_terminal_symbols = list(next_terminals_w_hist.keys())
    regex = _get_next_terminal_symbols_as_regex(next_terminal_symbols)

    # Get the chosen symbol as a string from the LLM.
    choice = mock_llm.get_choice(regex)

    # Get the symbol object.
    chosen_symbol = _retrace_symbol_obj_from_str(
        choice,
        next_terminal_symbols,
    )

    chosen_symbol_hist = next_terminals_w_hist[chosen_symbol]

    return chosen_symbol, chosen_symbol_hist


def animate_cfg_guide(cfg_grammar: str):
    cfg_guide_obj = CFGGuide(cfg_grammar)
    mock_llm = _MockLLM()

    max_num_plots = len(cfg_guide_obj.built_cfg_grammar.keys())

    figure, axes = plt.subplots(1, max_num_plots, figsize=(18, 10))

    # Create a text box for the string output.
    text_box = TextBox(plt.axes([0.1, 0.05, 0.8, 0.05]), "Output:")

    # Make room for the text box.
    figure.subplots_adjust(bottom=0.2)

    chosen_symbol, chosen_symbol_hist = None, None

    def animate(frame):
        nonlocal chosen_symbol, chosen_symbol_hist

        chosen_symbol, chosen_symbol_hist = _animate_get_guided_response(
            cfg_guide_obj, chosen_symbol, chosen_symbol_hist, mock_llm
        )

        if chosen_symbol_hist is None:
            anim.event_source.stop()
            return

        # Clear the axes at the beginning of each frame.
        for i in range(len(axes)):
            axes[i].clear()

        for i, cfg_stateful_graph in enumerate(chosen_symbol_hist):
            _setup_symbol_graph_networkx(
                cfg_stateful_graph.graph, cfg_stateful_graph.state, axes[i]
            )
            axes[i].set_title(f"[LEVEL {i}]")

        # Clear the axis.
        for i in range(len(chosen_symbol_hist), max_num_plots):
            axes[i].axis("off")

        text_box.set_val(mock_llm.response)

    anim = FuncAnimation(figure, animate, frames=250, interval=500, repeat=True)

    plt.show()
