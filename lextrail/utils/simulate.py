import random
from dataclasses import dataclass, field

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import TextBox

from lextrail.base import Symbol
from lextrail.guide import CFGGenerationState, CFGGuide
from lextrail.utils.draw import _setup_symbol_graph_networkx


@dataclass
class MockLLM:
    response: list[str] = field(default_factory=lambda: [])

    def get_choice(self, choices: list[Symbol]) -> list[Symbol]:
        choice = random.choice(choices)
        if choice.content == "END_DEF":
            self.response.append("")
            return [choice]
        self.response.append(choice.content[1:-1])
        return [choice]


def _get_full_guided_response(mcfg_guide: CFGGuide) -> str:
    LLM = MockLLM()
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

    return "".join(LLM.response)


def _get_partial_guided_response(
    cfg_guide_obj: CFGGuide,
    chosen_symbols: list[Symbol],
    chosen_states: list[CFGGenerationState],
    mock_llm: "MockLLM",
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


def simulate_cfg_guide(cfg_grammar: str, _SCALE: int = 4000):
    cfg_guide_obj = CFGGuide(cfg_grammar)

    mock_llm = MockLLM()

    max_num_plots = len(cfg_guide_obj._built_cfg_grammar.keys())

    figure, axes = plt.subplots(
        max_num_plots // 2 + 1, max_num_plots // 2 + 1, figsize=(18, 10)
    )

    # Adjust layout spaces.
    figure.subplots_adjust(bottom=0.1, wspace=0.1, hspace=0.5)

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

        m, n = 0, 0
        for m, cfg_stateful_graphs in enumerate(list(zip(*chosen_states))):
            for n, cfg_stateful_graph in enumerate(set(cfg_stateful_graphs)):
                _setup_symbol_graph_networkx(
                    cfg_stateful_graph.graph,
                    cfg_stateful_graph.state,
                    axes.flat[m + n],
                    _SCALE // len(axes.flat),
                )
                axes.flat[m + n].set_title(f"[LEVEL {m}.{n}]")

        # Clear the axis.
        for i in range(m + n, len(axes.flat)):
            axes.flat[i].axis("off")

        text_box.set_val("".join(mock_llm.response))

    anim = FuncAnimation(figure, animate, frames=250, interval=500, repeat=False)  # type: ignore

    plt.show()
