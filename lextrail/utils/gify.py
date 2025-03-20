import imageio
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.widgets import TextBox

from lextrail.base import CFGGenerationState, Symbol
from lextrail.guide.guide import CFGGuide
from lextrail.utils.draw import _setup_symbol_graph_networkx
from lextrail.utils.simulate import _get_partial_guided_response, _MockLLM


def gify_cfg_guide(cfg_grammar: str, _RATIO: int = 4000):
    cfg_guide_obj = CFGGuide(cfg_grammar)

    mock_llm = _MockLLM()

    max_num_plots = len(cfg_guide_obj._built_cfg_grammar.keys())

    frames = []

    figure, axes = plt.subplots(
        max_num_plots // 2 + 1, max_num_plots // 2 + 1, figsize=(18, 10)
    )

    # Create text box for the string output.
    text_box = TextBox(plt.axes([0.1, 0.05, 0.8, 0.05]), "Output:")  # type: ignore

    # Set cursor index.
    text_box.cursor_index = None  # type: ignore

    # Make room for text box.
    plt.subplots_adjust(bottom=0.2)

    chosen_symbols: list[Symbol] = []
    chosen_states: list[CFGGenerationState] = []

    while True:
        chosen_symbols, chosen_states = _get_partial_guided_response(
            cfg_guide_obj, chosen_symbols, chosen_states, mock_llm
        )

        if not chosen_states:
            break

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

        # Convert plot to image.
        figure.canvas.draw()
        image = np.frombuffer(figure.canvas.tostring_rgb(), dtype="uint8")  # type: ignore
        image = image.reshape(figure.canvas.get_width_height()[::-1] + (3,))
        frames.append(image)
        plt.close(figure)

    # Save frames as GIF.
    durations = [500] * len(frames)
    imageio.mimsave("animation.gif", frames, duration=durations, loop=0)
