import json
import os
import threading
import time

from csv import Error
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, overload

from lextrail.base import CFGStatefulGraph, LTDeque
from lextrail.guide import Guide, CFGStatefulGraph, CFGGuide
from lextrail.helpers import LTContext, _get_symbols_from_generated_symbol_graph
from lextrail.utils.simulate import MockLLM, _get_partial_guided_response

VizGraph = dict[str, list[dict[str, str]]]

VizUpdate = dict[str, Any]

DEFAULT_STATE = {
    "results": [],
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
            if self.settings["paused"]:
                print("Simulation has been paused.")
                while self.settings["paused"] and not self.settings["interrupted"]:
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

            if all(isinstance(x, CFGStatefulGraph) for x in curr_states):
                # [NOTE] Throw an error if `curr_states` is empty? Or make an empty CFGGuide/Guide valid?
                curr_states = [LTDeque([state]) for state in curr_states]
            # elif all(isinstance(x, CFGStatefulGraph) for curr_state in curr_states for x in curr_state):
            #     curr_states_ = curr_states

            self.state["results"].append([curr_state_.serialize() for curr_state_ in curr_states])

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
        elif self.path == "/vis-network.min.js":
            self.send_response(200)
            self.send_header("Content-type", "application/javascript")
            self.end_headers()
            
            # Read the actual file from your filesystem
            current_dir = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(current_dir, f"libs/vis-network.min.js"), 'rb') as f:
                self.wfile.write(f.read())

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
