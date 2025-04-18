import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from copy import deepcopy

sys.path.append("/home/achraf/lextrail")

from lextrail.base import CFGStatefulGraph, Symbol, SymbolGraph
from lextrail.guide import CFGGenerationState, CFGGuide
from lextrail.helpers import _get_symbols_from_generated_symbol_graph
from lextrail.utils.simulate import _get_partial_guided_response, _MockLLM

VizGraph = dict[str, list[dict[str, str]]]

VizUpdate = dict[str, Any]

DEFAULT_STATE = {
    "updates": [],
    "rollbacks": [],
    "response": [],
    "is_complete": False,
}

DEFAULT_SETTINGS = {
    "paused": False,
    "interrupted": False,
    "reset": False,
    "speed": 0.5,  # Default 500ms delay.
}


def _symbol_graph_to_vis_network(
    symbol_graph: SymbolGraph,
) -> VizGraph:
    nodes: list[dict[str, str]] = []
    edges: list[dict[str, str]] = []

    symbols = _get_symbols_from_generated_symbol_graph(symbol_graph)

    for symbol in symbols.values():
        nodes.append(
            {
                "id": str(symbol.s_id),
                "label": symbol.content,
                "color": "lightblue",
                # "size": 10,
            }
        )

    for symbol, successors in symbol_graph.tree.items():
        fromId = str(symbol.s_id)
        for successor in successors:
            to_id = str(successor.s_id)
            edges.append({"from": fromId, "to": to_id, "color": "gray"})

    return {"nodes": nodes, "edges": edges}


def _extract_update(
    *, prev_states: list[CFGStatefulGraph], curr_states: list[CFGStatefulGraph]
) -> VizUpdate:
    movu: dict[int, dict[str, str]] = {}
    addu: dict[int, VizGraph] = {}
    delu: dict[int, VizGraph] = {}

    min_len = min(len(prev_states), len(curr_states))
    for i in range(min_len):
        prev, curr = prev_states[i], curr_states[i]
        if prev != curr:
            if prev.graph == curr.graph:
                assert (
                    prev.state is not None and curr.state is not None
                ), f"Invalid states for either {prev} or {curr}."
                movu[i] = {str(prev.state.s_id): str(curr.state.s_id)}
            else:
                delu[i] = _symbol_graph_to_vis_network(prev_states[i].graph)
                addu[i] = _symbol_graph_to_vis_network(curr_states[i].graph)
                assert curr.state is not None, f"Invalid state for {curr}."
                movu[i] = {"": str(curr.state.s_id)}

    # Handle deletions (prev longer than curr).
    if len(prev_states) > len(curr_states):
        for i in range(min_len, len(prev_states)):
            prev = prev_states[i]
            delu[i] = _symbol_graph_to_vis_network(prev.graph)
            assert prev.state is not None, f"Invalid state for {prev}."
            movu[i] = {str(prev.state.s_id): ""}

    # Handle additions (curr longer than prev).
    elif len(prev_states) < len(curr_states):
        for i in range(min_len, len(curr_states)):
            curr = curr_states[i]
            addu[i] = _symbol_graph_to_vis_network(curr.graph)
            assert curr.state is not None, f"Invalid state for {curr}."
            movu[i] = {"": str(curr.state.s_id)}

    return {"addu": addu, "movu": movu, "delu": delu}


def _to_rollback(vizupdate: VizUpdate) -> VizUpdate:
    return {
        "addu": vizupdate["delu"],
        "movu": {
            index: {
                v: k for k, v in ids.items() if k
            }  # Only inverse moves with valid `fromId`.
            for index, ids in vizupdate["movu"].items()
        },
        "delu": vizupdate["addu"],
    }


class Simulate:
    guide: CFGGuide  # [TODO] Add support for Guide.
    state: dict[str, Any]
    settings: dict[str, Any]

    def __init__(self, cfg_grammar: str):
        self.guide = CFGGuide(cfg_grammar)
        self.state = deepcopy(DEFAULT_STATE)
        self.settings = deepcopy(DEFAULT_SETTINGS)

    def run(self, port=8000):
        # Run the backend as a thread.
        self.simulation = threading.Thread(target=self.get_next_state, daemon=True)
        self.simulation.start()

        # Run the server.
        server_address = ("localhost", port)
        SimpleServer.initiate(self)
        httpd = HTTPServer(server_address, SimpleServer)
        print(f"Server running at http://localhost:{port}")
        httpd.serve_forever()

    def get_next_state(self):
        mock_llm = _MockLLM()
        chosen_symbols: list[Symbol] = []
        chosen_states: list[CFGGenerationState] = []

        prev_states = []
        while True:
            curr_states = []
            # Check if the simulation is interrupted.
            if self.settings["interrupted"]:
                print("Simulation has been interrupted.")
                break

            # Check if the simulation is paused.
            while self.settings["paused"] and not self.settings["interrupted"]:
                time.sleep(0.1)

            # [TODO] Check if the simulation is reset.
            if self.settings["reset"]:
                print("Simulation has been reset.")
                prev_states = []
                # Reset the states and settings.
                self.state, self.settings = (
                    deepcopy(DEFAULT_STATE),
                    deepcopy(DEFAULT_SETTINGS),
                )
                # Reset CFGGuide.
                chosen_symbols, chosen_states = [], []
                # Reset response.
                mock_llm.response = []

            chosen_symbols, chosen_states = _get_partial_guided_response(
                self.guide, chosen_symbols, chosen_states, mock_llm
            )

            self.state["response"] = mock_llm.response

            if not chosen_states:
                print("Simulation is complete, no more states to process.")
                self.state["is_complete"] = True
                # Run proceeds in case of a reset.
                while not self.settings["reset"]:
                    time.sleep(0.1)
                continue

            for m, cfg_stateful_graphs in enumerate(list(zip(*chosen_states))):
                for n, cfg_stateful_graph in enumerate(set(cfg_stateful_graphs)):
                    curr_states.append(cfg_stateful_graph)

            _next_update = _extract_update(
                prev_states=prev_states, curr_states=curr_states
            )

            self.state["updates"].append(_next_update)
            self.state["rollbacks"].append(_to_rollback(_next_update))

            prev_states = curr_states

            # Add delay based on speed setting.
            if self.settings["speed"] > 0:
                time.sleep(self.settings["speed"])


class SimpleServer(BaseHTTPRequestHandler):
    @classmethod
    def initiate(cls, simulate: Simulate):
        cls.simulate = simulate

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(self.get_html_content().encode())
        elif self.path == "/graph":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response_data = {
                "updates": self.simulate.state["updates"],
                "rollbacks": self.simulate.state["rollbacks"],
                "_response": self.simulate.state["response"],
                "_is_simulation_complete": self.simulate.state["is_complete"],
                "_is_paused": self.simulate.settings["paused"],
                "_is_interrupted": self.simulate.settings["interrupted"],
            }
            self.wfile.write(json.dumps(response_data).encode())

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode("utf-8"))
        if self.path == "/control":
            # Handle the control commands.
            if "action" in data:
                if data["action"] == "pause":
                    self.simulate.settings["paused"] = True
                elif data["action"] == "resume":
                    self.simulate.settings["paused"] = False
                elif data["action"] == "toggle_pause":
                    self.simulate.settings["paused"] = not self.simulate.settings[
                        "paused"
                    ]
                elif data["action"] == "interrupt":
                    self.simulate.settings["interrupted"] = True
                    self.simulate.settings["paused"] = False
                elif data["action"] == "reset":
                    self.simulate.settings["interrupted"] = False
                    self.simulate.settings["paused"] = False
                    self.simulate.settings["reset"] = True
                elif data["action"] == "set_speed":
                    if "rate" in data and isinstance(data["rate"], (int, float)):
                        self.simulate.settings["speed"] = data["rate"]
            # Send response.
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"status": "success", "state": self.simulate.settings}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def get_html_content(self: "SimpleServer") -> str:
        contents: list[str] = []
        current_dir = os.path.dirname(os.path.abspath(__file__))
        for filename in ["index.html", "style.css", "script.js"]:
            with open(os.path.join(current_dir, filename)) as f:
                contents.append(f.read())
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Graph Visualization Tool</title>
            <script src="https://unpkg.com/vis-network@latest/dist/vis-network.min.js"></script>
            <link href="https://unpkg.com/vis-network@latest/dist/vis-network.min.css" rel="stylesheet" type="text/css" />
            <style>
        {contents[1]}
            </style>
        </head>
        <body>
        {contents[0]}
            <script>
        {contents[2]}
            </script>
        </body>
        </htm
        """


def run_server(port=8000):
    server_address = ("localhost", port)
    httpd = HTTPServer(server_address, SimpleServer)
    print(f"Server running at http://localhost:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    cfg_grammar = r"""
    start: expression
    expression: term (("+" | "-") term)+
    term: factor (("*" | "/") factor "^" /-?[0-1]/)+
    factor: NUMBER
    NUMBER: /[0-1]\.[0-1]/
    """
    Simulate(cfg_grammar=cfg_grammar).run()
