import imageio
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.widgets import TextBox

from lextrail.guide.guide import CFGGuide
from lextrail.render.draw import _setup_symbol_graph_networkx
from lextrail.render.simulate import _get_partial_guided_response, _MockLLM


def gify_cfg_guide(cfg_grammar: str):
    cfg_guide_obj = CFGGuide(cfg_grammar)
    mock_llm = _MockLLM()

    max_num_plots = len(cfg_guide_obj.built_cfg_grammar.keys())
    frames = []

    # Create a figure with extra space for the text box
    figure, axes = plt.subplots(1, max_num_plots, figsize=(18, 11))

    # Create text box
    text_box_ax = plt.axes([0.1, 0.05, 0.8, 0.05])  # type: ignore
    text_box = TextBox(text_box_ax, "Output:")

    # Set cursor index
    text_box.cursor_index = None  # type: ignore

    # Adjust layout to make room for text box
    plt.subplots_adjust(bottom=0.2)

    chosen_symbol, chosen_symbol_hist = None, None

    while True:
        chosen_symbol, chosen_symbol_hist = _get_partial_guided_response(
            cfg_guide_obj, chosen_symbol, chosen_symbol_hist, mock_llm
        )

        if chosen_symbol_hist is None:
            break

        # Clear previous plot
        for ax in axes:
            ax.clear()

        for i, cfg_stateful_graph in enumerate(chosen_symbol_hist):
            _setup_symbol_graph_networkx(
                cfg_stateful_graph.graph, cfg_stateful_graph.state, axes[i]
            )
            axes[i].set_title(f"[LEVEL {i}]")

        # Clear unused axes
        for i in range(len(chosen_symbol_hist), max_num_plots):
            axes[i].axis("off")

        # Update text box with LLM response
        text_box.set_val(mock_llm.response)

        # Convert plot to image
        figure.canvas.draw()
        image = np.frombuffer(figure.canvas.tostring_rgb(), dtype="uint8")  # type: ignore
        image = image.reshape(figure.canvas.get_width_height()[::-1] + (3,))
        frames.append(image)

        plt.close(figure)

    # Save frames as GIF
    durations = [500] * len(frames)
    imageio.mimsave("animation.gif", frames, duration=durations, loop=0)
