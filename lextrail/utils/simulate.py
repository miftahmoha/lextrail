import random
from dataclasses import dataclass, field

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import TextBox

from lextrail.base import Symbol
from lextrail.guide import CFGGenerationState, CFGGuide
from lextrail.utils.draw import _setup_symbol_graph_networkx


@dataclass
class _MockLLM:
    response: str = field(default="")

    def get_choice(self, choices: list[Symbol]) -> list[Symbol]:
        choice = random.choice(choices)
        if choice.content == "END_DEF":
            return [choice]
        self.response += choice.content[1:-1]
        return [choice]


def _get_full_guided_response(mcfg_guide: CFGGuide) -> str:
    LLM = _MockLLM()
    chosen_symbols: list[Symbol] = []
    chosen_states: list[CFGGenerationState] = []

    while True:
        mcfg_guide.get_next_terminals(chosen_symbols, chosen_states)
        next_terminals_w_hist = mcfg_guide.next_terminals_w_states

        # End generation.
        if not next_terminals_w_hist:
            break

        next_terminal_symbols = list(next_terminals_w_hist.keys())

        # Get the chosen symbol as a string from the LLM.
        chosen_symbols = LLM.get_choice(next_terminal_symbols)

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
    next_terminals_w_states = cfg_guide_obj.next_terminals_w_states

    # End generation.
    if not next_terminals_w_states:
        return [], []

    next_terminal_symbols = list(next_terminals_w_states.keys())

    # Get the chosen symbol as a string from the LLM.
    chosen_symbols = mock_llm.get_choice(next_terminal_symbols)

    chosen_states = [
        next_terminals_w_states[chosen_symbol] for chosen_symbol in chosen_symbols
    ]

    return chosen_symbols, chosen_states


def simulate_cfg_guide(cfg_grammar: str, _RATIO: int = 4000):
    cfg_guide_obj = CFGGuide(cfg_grammar)

    mock_llm = _MockLLM()

    max_num_plots = len(cfg_guide_obj._built_cfg_grammar.keys())

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
