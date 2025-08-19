import json
import os
import threading
import time

from csv import Error
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, KeysView, overload

from lextrail.base import CFGStatefulGraph, Symbol, SymbolGraph, SymbolType, LTDeque
from lextrail.guide import Guide, CFGStatefulGraph, CFGGuide
from lextrail.helpers import LTContext, _get_symbols_from_generated_symbol_graph
from lextrail.utils.simulate import MockLLM, _get_partial_guided_response

VizGraph = dict[str, list[dict[str, str]]]

VizUpdate = dict[str, Any]

DEFAULT_STATE = {
    "updates": [],
    "rollbacks": [],
    "previews": [],
    "response": [],
    "completed": False,
}

DEFAULT_SETTINGS = {
    "paused": False,
    "interrupted": False,
    "reset": False,
    "speed": 1,  # Default 1000ms delay.
    "run": 1,
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
            }
        )

    for symbol, successors in symbol_graph.tree.items():
        fromId = str(symbol.s_id)
        for successor in successors:
            to_id = str(successor.s_id)
            edges.append({"from": fromId, "to": to_id, "color": "gray"})

    return {"nodes": nodes, "edges": edges}


def _extract_preview(next_symbols: KeysView[Symbol]) -> list[str]:
    preview_ids: list[str] = []

    for next_symbol in next_symbols:
        preview_ids.append(str(next_symbol.s_id))

    return preview_ids


# [NOTE] We use `LTDeque` for both `Guide` and `CFGGuide`, `CFGStatefulGraph` needs to be wrapped 
# into a `LTDeque` for `Guide`. 
def _extract_update(
    *, prev_states: LTDeque[CFGStatefulGraph], curr_states: LTDeque[CFGStatefulGraph]
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
                movu[i] = {"from": str(prev.state.s_id), "to": str(curr.state.s_id)}
            else:
                delu[i] = _symbol_graph_to_vis_network(prev_states[i].graph)
                addu[i] = _symbol_graph_to_vis_network(curr_states[i].graph)
                assert curr.state is not None, f"Invalid state for {curr}."
                movu[i] = {"from": "", "to": str(curr.state.s_id)}
        else:
            assert (
                prev.state is not None and curr.state is not None
            ), f"Invalid states for either {prev} or {curr}."
            movu[i] = {"from": str(prev.state.s_id), "to": str(curr.state.s_id)}

    # Handle deletions (prev longer than curr).
    if len(prev_states) > len(curr_states):
        for i in range(min_len, len(prev_states)):
            prev = prev_states[i]
            delu[i] = _symbol_graph_to_vis_network(prev.graph)
            assert prev.state is not None, f"Invalid state for {prev}."
            movu[i] = {"from": str(prev.state.s_id), "to": ""}

    # Handle additions (curr longer than prev).
    elif len(prev_states) < len(curr_states):
        for i in range(min_len, len(curr_states)):
            curr = curr_states[i]
            addu[i] = _symbol_graph_to_vis_network(curr.graph)
            assert curr.state is not None, f"Invalid state for {curr}."
            movu[i] = {"from": "", "to": str(curr.state.s_id)}

    return {"addu": addu, "movu": movu, "delu": delu}


def _to_rollback(vizupdate: VizUpdate) -> VizUpdate:
    return {
        "addu": vizupdate["delu"],
        "movu": {
            index: {"from": ids["to"], "to": ids["from"]}
            for index, ids in vizupdate["movu"].items()
        },
        "delu": vizupdate["addu"],
    }

class Simulate:
    state: dict[str, Any]
    settings: dict[str, Any]

    # [TODO] Can an abstract class remove overload?
    @overload
    def __init__(self: "Simulate", guide: Guide) -> None: ...

    @overload
    def __init__(self: "Simulate", guide: CFGGuide) -> None: ...

    def __init__(self, guide) -> None:
        self.guide = guide
        self.state = deepcopy(DEFAULT_STATE)
        self.settings = deepcopy(DEFAULT_SETTINGS)

    def run(self, port=8000):
        # Run the backend as a thread.
        self.simulation = threading.Thread(target=self.get_next_state, daemon=True)
        self.simulation.start()

        # Run the server.
        server_address = ("localhost", port)
        Server.initiate(self)
        httpd = HTTPServer(server_address, Server)
        print(f"Server running at http://localhost:{port}")
        httpd.serve_forever()

    def get_next_state(self):
        mock_llm = MockLLM()

        curr_symbols, curr_states = [], []
        prev_states = []
        while True:
            # Check if the simulation is interrupted.
            if self.settings["interrupted"]:
                print("Simulation has been interrupted.")
                self.state["interrupted"] = True
                # Run proceeds in case of a reset.
                while not self.settings["reset"]:
                    time.sleep(0.1)
                continue
 
            # Check if the simulation is paused.
            while self.settings["paused"] and not self.settings["interrupted"]:
                print("Simulation has been paused.")
                time.sleep(0.1)

            # [TODO] Check if the simulation is reset.
            if self.settings["reset"]:
                print("Simulation has been reset.")
                # Set the id for the next run.
                next_run = self.settings["run"] + 1    
                # Reset the states and settings.
                prev_states = []      
                self.state, self.settings = (
                    deepcopy(DEFAULT_STATE),
                    deepcopy(DEFAULT_SETTINGS),
                )
                # Reset Guide/CFGGuide.
                curr_symbols, curr_states = [], []
                # Reset response.
                mock_llm.response = []
                # Increment run.
                self.settings["run"] = next_run

            curr_symbols, curr_states = _get_partial_guided_response(
                self.guide, deepcopy(curr_symbols), deepcopy(curr_states), mock_llm
            )
            self.state["response"] = mock_llm.response

            if not curr_states:
                print("Simulation is complete, no more states to process.")
                self.state["completed"] = True
                # Run proceeds in case of a reset.
                while not self.settings["reset"]:
                    time.sleep(0.1)
                continue

            _next_update, _next_rollback = [], []
            _next_preview = _extract_preview(self.guide.next_terminals_w_states.keys())

            # `prev_states` is ambiguous, then it'll either be a List[CFGStatefulGraph]
            #  or List[LTDeque[CFGStatefulGraph]].
            curr_states_, prev_states_ = [], []
            if len(prev_states) > 1:   
                # When `curr_state` is `CFGStatefulGraph` from `Guide`, then `prev_states` should
                # be List[CFGStatefulGraph].
                if isinstance(curr_states, list) and all(isinstance(x, CFGStatefulGraph) for x in curr_states):
                    curr_states_ = [LTDeque([state]) for state in curr_states]
                    # Cast each element in `prev_states`into the right type.
                    prev_states_ = [LTDeque([state]) for state in prev_states]
                elif all(isinstance(x, CFGStatefulGraph) for curr_state in curr_states for x in curr_state):
                    curr_states_, prev_states_ = curr_states, prev_states

                for curr_state in curr_states_:          
                    # Match the correct previous state to the current (chosen) state, we've got 
                    # to backtrack the antecedents in the current state until it matches the node
                    # at which we left in the previous state. 

                    # If we're dealing with CFGGuide, backtracking goes through the layers in LTDeque,
                    # if the antecedent of some node is `None`, then we go to the layer underneath.
                    # Then, we keep going until we reach a layer which state has a valid
                    # source, if it's a non-terminal symbol, we backtrack until we get to a terminal
                    # symbol.
                    prev_symbol = curr_state[-1].state.s_metadata["_SRC"]

                    k = 1
                    while not prev_symbol:
                        prev_symbol = curr_state[-1 - k].state.s_metadata[
                            "_SRC"
                        ]
                        k += 1

                        if k == len(curr_state):
                            raise Error("Simulator Error: Backtracking didn't lead to a symbol source.")

                    while prev_symbol.s_type == SymbolType.NON_TERMINAL:
                        prev_symbol = prev_symbol.s_metatadata["_SRC"]

                    if prev_symbol.s_type not in [
                            SymbolType.TERMINAL,
                        ]:
                        raise Error("Simulator Error: Backtracking didn't lead to a terminal symbol source.")

                    # Then we compare with the last node where we left in the previous state 
                    # `prev_state[-1].state`, WHICH can't be a non-terminal symbol, since ambiguity
                    # occurs at terminal symbols with the same content. 
                    # `Guide` is trivial since it deals with terminal symbols only.
                    btrk_state = next((prev_state for prev_state in prev_states_ if prev_symbol == prev_state[-1].state), None)
                    if btrk_state is None:
                        raise Error("Simulator Error: Backtracking couldn't associate a source from the previous frame.")

                    viz_update =  _extract_update(
                            prev_states=btrk_state, curr_states=curr_state
                        )
                    
                    _next_update.append(viz_update)
                    _next_rollback.append(_to_rollback(viz_update))
            else:
                if all(isinstance(x, CFGStatefulGraph) for x in curr_states):
                    # [NOTE] Throw an error if `curr_states` is empty? Or make an empty CFGGuide/Guide valid?
                    curr_states_ = [LTDeque([state]) for state in curr_states]
                    # Cast each element in `prev_states` into the right type.
                    prev_states_ = LTDeque([prev_states[0]]) if prev_states else LTDeque([])
                elif all(isinstance(x, CFGStatefulGraph) for curr_state in curr_states for x in curr_state):
                    curr_states_ = curr_states
                    prev_states_ = prev_states[0] if prev_states else LTDeque([])

                for curr_state in curr_states_:
                    viz_update = _extract_update(
                            prev_states=prev_states_,
                            curr_states=curr_state,
                        )

                    _next_update.append(viz_update)
                    _next_rollback.append(_to_rollback(viz_update))

            self.state["updates"].append(_next_update)
            self.state["rollbacks"].append(_next_rollback)
            self.state["previews"].append(_next_preview)

            prev_states = curr_states

            # Add delay based on speed setting.
            if self.settings["speed"] > 0:
                time.sleep(self.settings["speed"])


class Server(BaseHTTPRequestHandler):
    simulate: "Simulate"

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
                "data": self.simulate.state,
                "setting": self.simulate.settings,
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
                elif data["action"] == "delay":
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

    def get_html_content(self: "Server") -> str:
        contents: list[str] = []

        current_dir = os.path.dirname(os.path.abspath(__file__))

        for filename in ["index.html", "style.css", "script.js"]:
            with open(os.path.join(current_dir, f"build/{filename}")) as f:
                contents.append(f.read())

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
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
    httpd = HTTPServer(server_address, Server)
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
    cfgguide_ = CFGGuide(cfg_grammar)
    guide_ = Guide('"term" "ambiguity_1"* "ambiguity" "finish"')
    with LTContext(SPLIT_CHARS="1", PARSE_REGEX="1"):
        Simulate(guide_).run()
