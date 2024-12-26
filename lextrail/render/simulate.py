import re
import random
import warnings
from typing import Optional
from dataclasses import dataclass, field


import exrex
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import TextBox

from lextrail.base import Symbol, SymbolType
from lextrail.helpers import _is_end_def_symbol
from lextrail.guide.guide import CFGGuide, CFGGenerationState
from lextrail.render.draw import _setup_symbol_graph_networkx
from lextrail.exceptions import ParsingError


def _validate_regex(string: str, pattern: str) -> bool:
    regex = re.compile(pattern)
    if regex.fullmatch(string):
        return True
    return False


def _map_str_to_symbol(
    chosen_symbol_str: str,
    next_terminal_symbols: list[Symbol],
) -> Symbol:
    chosen_symbols: list[Symbol] = []

    for symbol in next_terminal_symbols:
        if symbol.s_type == SymbolType.REGEX:
            if _validate_regex(chosen_symbol_str, symbol.content):
                chosen_symbols.append(symbol)
        elif symbol.s_type == SymbolType.TERMINAL:
            if symbol.content[1:-1] == chosen_symbol_str:
                chosen_symbols.append(symbol)
        elif _is_end_def_symbol(symbol):
            if symbol.content == chosen_symbol_str:
                chosen_symbols.append(symbol)
        else:
            raise ParsingError(
                f"{symbol.s_type} is invalid, only {SymbolType.TERMINAL} or {SymbolType.REGEX} are valid."
            )

    # [TODO?] Interactive.
    if len(chosen_symbols) > 2:
        warnings.warn(
            "Chosen symbol present in multiple paths, one will be picked with equal probability."
        )
        chosen_symbol = random.choice(chosen_symbols)
        return chosen_symbol

    return chosen_symbols[0]


def _map_next_terminal_symbols_to_regex(
    symbols: list[Symbol],
) -> str:
    regexes: list[str] = []

    for symbol in symbols:
        if symbol.s_type == SymbolType.TERMINAL:
            regexes.append(re.escape(symbol.content[1:-1]))
        elif symbol.s_type == SymbolType.REGEX:
            regexes.append(symbol.content)
        elif _is_end_def_symbol(symbol):
            regexes.append(re.escape(symbol.content))
        else:
            raise ParsingError(
                f"{symbol.s_type} is invalid, only {SymbolType.TERMINAL} or {SymbolType.REGEX} are valid."
            )

    return r"(" + r"|".join([r"(" + x + r")" for x in regexes]) + r")"


@dataclass
class _MockLLM:
    response: str = field(default="")

    # Use `exrex` to generate a sample from a REGEX expression.
    def get_choice(self, regex: str) -> str:
        choice = exrex.getone(regex)
        if choice == "END_DEF":
            return choice
        self.response += choice
        return choice


def _get_full_guided_response(cfg_guide: CFGGuide) -> str:
    mock_llm = _MockLLM()
    chosen_symbol: Optional[Symbol] = None
    chosen_symbol_hist: CFGGenerationState = None

    while True:
        cfg_guide.get_next_terminals(chosen_symbol_hist, chosen_symbol)
        next_terminals_w_hist = cfg_guide.next_terminals_w_history

        # End generation.
        if not next_terminals_w_hist:
            break

        next_terminal_symbols = list(next_terminals_w_hist.keys())
        regex = _map_next_terminal_symbols_to_regex(next_terminal_symbols)

        # Get the chosen symbol as a string from the LLM.
        choice = mock_llm.get_choice(regex)

        # Get the symbol object.
        chosen_symbol = _map_str_to_symbol(
            choice,
            next_terminal_symbols,
        )

        chosen_symbol_hist = next_terminals_w_hist[chosen_symbol]

    return mock_llm.response


def _get_partial_guided_response(
    cfg_guide_obj: CFGGuide, chosen_symbol, chosen_symbol_hist, mock_llm: "_MockLLM"
) -> tuple[Optional[Symbol], CFGGenerationState]:
    cfg_guide_obj.get_next_terminals(chosen_symbol_hist, chosen_symbol)
    next_terminals_w_hist = cfg_guide_obj.next_terminals_w_history

    # End generation.
    if not next_terminals_w_hist:
        return None, None

    next_terminal_symbols = list(next_terminals_w_hist.keys())
    regex = _map_next_terminal_symbols_to_regex(next_terminal_symbols)

    # Get the chosen symbol as a string from the LLM.
    choice = mock_llm.get_choice(regex)

    # Get the symbol object.
    chosen_symbol = _map_str_to_symbol(
        choice,
        next_terminal_symbols,
    )

    chosen_symbol_hist = next_terminals_w_hist[chosen_symbol]

    return chosen_symbol, chosen_symbol_hist


def simulate_cfg_guide(cfg_grammar: str):
    cfg_guide_obj = CFGGuide(cfg_grammar)
    mock_llm = _MockLLM()

    max_num_plots = len(cfg_guide_obj.built_cfg_grammar.keys())

    figure, axes = plt.subplots(1, max_num_plots, figsize=(18, 10))

    # Create a text box for the string output.
    text_box = TextBox(plt.axes([0.1, 0.05, 0.8, 0.05]), "Output:")  # type: ignore

    # Set cursor index.
    text_box.cursor_index = None  # type: ignore

    # Make room for the text box.
    figure.subplots_adjust(bottom=0.2)

    chosen_symbol, chosen_symbol_hist = None, None

    def animate(frame):
        nonlocal chosen_symbol, chosen_symbol_hist

        chosen_symbol, chosen_symbol_hist = _get_partial_guided_response(
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

    anim = FuncAnimation(figure, animate, frames=250, interval=500, repeat=False)  # type: ignore

    plt.show()
