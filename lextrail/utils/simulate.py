import re
from dataclasses import dataclass, field

import exrex
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import TextBox

from lextrail.base import Symbol, SymbolType
from lextrail.exceptions import ParsingError
from lextrail.guide.guide import CFGGenerationState, CFGGuide
from lextrail.helpers import _is_end_def_symbol
from lextrail.utils.draw import _setup_symbol_graph_networkx


def _validate_regex(string: str, pattern: str) -> bool:
    regex = re.compile(pattern)
    if regex.fullmatch(string):
        return True
    return False


def _map_str_to_symbol(
    chosen_symbol_str: str,
    next_terminal_symbols: list[Symbol],
) -> list[Symbol]:
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

    return chosen_symbols


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


def _get_full_guided_response(mcfg_guide: CFGGuide) -> str:
    LLM = _MockLLM()
    chosen_symbols: list[Symbol] = []
    chosen_states: list[CFGGenerationState] = []

    while True:
        mcfg_guide.get_next_terminals(chosen_symbols, chosen_states)
        next_terminals_w_hist = mcfg_guide.next_terminals_w_history

        # End generation.
        if not next_terminals_w_hist:
            break

        next_terminal_symbols = list(next_terminals_w_hist.keys())
        regex = _map_next_terminal_symbols_to_regex(next_terminal_symbols)

        # Get the chosen symbol as a string from the LLM.
        choice = LLM.get_choice(regex)

        # Get the symbol object.
        chosen_symbols = _map_str_to_symbol(
            choice,
            next_terminal_symbols,
        )

        chosen_states = [
            next_terminals_w_hist[chosen_symbol] for chosen_symbol in chosen_symbols
        ]

    return LLM.response


def _get_partial_guided_response(
    cfg_guide_obj: CFGGuide,
    chosen_symbols: list[Symbol],
    chosen_states: list[CFGGenerationState],
    mock_llm: "_MockLLM",
    ):
    cfg_guide_obj.get_next_terminals(chosen_symbols, chosen_states)
    next_terminals_w_history = cfg_guide_obj.next_terminals_w_history

    # End generation.
    if not next_terminals_w_history:
        return [], [] 

    next_terminal_symbols = list(next_terminals_w_history.keys())
    regex = _map_next_terminal_symbols_to_regex(next_terminal_symbols)

    # Get the chosen symbol as a string from the LLM.
    choice = mock_llm.get_choice(regex)

    # Get the symbol object.
    chosen_symbols = _map_str_to_symbol(
        choice,
        next_terminal_symbols,
    )

    chosen_states = [
        next_terminals_w_history[chosen_symbol] for chosen_symbol in chosen_symbols
    ]

    return chosen_symbols, chosen_states


def simulate_cfg_guide(cfg_grammar: str, _RATIO: int = 4000):
    cfg_guide_obj = CFGGuide(cfg_grammar)

    mock_llm = _MockLLM()

    max_num_plots = len(cfg_guide_obj.built_cfg_grammar.keys())

    figure, axes = plt.subplots(
        max_num_plots // 2 + 1, max_num_plots // 2 + 1, figsize=(18, 10)
    )

    # Create a text box for the string output.
    text_box = TextBox(plt.axes([0.1, 0.05, 0.8, 0.05]), "Output:")  # type: ignore

    # Set cursor index.
    text_box.cursor_index = None  # type: ignore

    # Make room for the text box.
    figure.subplots_adjust(bottom=0.2)

    chosen_symbols: list[Symbol] = []
    chosen_states: list[CFGGenerationState] = []

    def animate(frame):
        nonlocal chosen_symbols, chosen_states

        chosen_symbols, chosen_states = _get_partial_guided_response(
            cfg_guide_obj, chosen_symbols, chosen_states, mock_llm
        )

        if not chosen_states:
            anim.event_source.stop()
            return

        for i in range(len(axes.flat)):
            axes.flat[i].clear()

        for m, cfg_stateful_graphs in enumerate(list(zip(*chosen_states))):
            for n, cfg_stateful_graph in enumerate(set(cfg_stateful_graphs)):
                _setup_symbol_graph_networkx(
                    cfg_stateful_graph.graph,
                    cfg_stateful_graph.state,
                    axes.flat[m + n],
                    _RATIO // len(axes.flat),
                )
                axes.flat[m + n].set_title(f"[LEVEL {m}.{n}]")

        # Clear the axis.
        for i in range(m + n, len(axes.flat)):  # type: ignore
            axes.flat[i].axis("off")

        text_box.set_val(mock_llm.response)

    anim = FuncAnimation(figure, animate, frames=250, interval=500, repeat=False)  # type: ignore

    plt.show()
