import json
import random
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from lextrail.guide import Trail, trail_run


@dataclass
class UI_Context:
    state: dict[str, Any] = field(
        default_factory=lambda: {
            "results": [],
            "response": [],
            "completed": False,
        }
    )
    settings: dict[str, Any] = field(
        default_factory=lambda: {
            "paused": False,
            "interrupted": False,
            "reset": False,
            "run": 1,
        }
    )


def run_simulation(core: Trail, ui: UI_Context):
    ui_state, ui_settings = ui.state, ui.settings

    while True:
        if ui_settings["interrupted"]:
            print("Simulation has been interrupted.")

            ui_state["interrupted"] = True
            break

        if ui_settings["paused"]:
            print("Simulation has been paused.")

            while ui_settings["paused"]:
                time.sleep(0.1)

        if ui_settings["reset"]:
            print("Simulation has been reset.")

            # Avoids the gap where the states from TS and Python mismatch.
            next_run = ui_settings["run"] + 1

            ui.state, ui.settings = (
                {
                    "results": [],
                    "response": [],
                    "completed": False,
                },
                {
                    "paused": False,
                    "interrupted": False,
                    "reset": False,
                    "run": 1,
                },
            )

            ui_state, ui_settings = ui.state, ui.settings
            ui_settings["run"] = next_run

            core.state.proposals = []

        trail_run(core)

        proposals = core.state.proposals

        if not proposals:
            print("Simulation is complete, no more states to process.")
            ui_state["completed"] = True

            # Run proceeds in case of a reset.
            while not ui_settings["reset"]:
                time.sleep(0.1)

            continue

        next_value = random.choice(proposals).value

        # Recover ambiguous proposals.
        proposals = [proposal for proposal in proposals if proposal.value == next_value]

        if proposals:
            ui_state["response"] += [proposals[-1].value]

        core.state.proposals = proposals

        frames = [proposal.frame for proposal in proposals]

        ui_state["results"].append(
            [[layer.serialize() for layer in frame] for frame in frames]
        )


def run_playground(trail: Trail, port=8000):
    ui = UI_Context()

    simulation = threading.Thread(target=run_simulation, args=(trail, ui), daemon=True)
    simulation.start()

    server_address = ("localhost", port)
    Server.initiate(ui)
    httpd = HTTPServer(server_address, Server)
    print(f"Server running at http://localhost:{port}")
    httpd.serve_forever()


class Server(BaseHTTPRequestHandler):
    ui: UI_Context

    @classmethod
    def initiate(cls, ui: UI_Context):
        cls.ui = ui

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

            self.wfile.write(
                json.dumps(
                    {
                        "data": self.ui.state,
                        "setting": self.ui.settings,
                    }
                ).encode()
            )

        elif self.path == "/vis-network.min.js":
            self.send_response(200)
            self.send_header("Content-type", "application/javascript")
            self.end_headers()

            with open(
                Path(__file__).parent.parent / "playground" / "vis/vis-network.min.js",
                "rb",
            ) as f:
                self.wfile.write(f.read())

        elif self.path == "/favicon.ico":
            self.send_response(200)
            self.send_header("Content-type", "application/javascript")
            self.end_headers()

            with open(
                Path(__file__).parent.parent / "playground" / "favicon.png", "rb"
            ) as f:
                self.wfile.write(f.read())

    def do_POST(self):
        size = int(self.headers["Content-Length"])
        content = self.rfile.read(size)
        data = json.loads(content.decode("utf-8"))

        action = data.get("action")
        settings = self.ui.settings

        if self.path == "/control":
            if "action" in data:
                if action == "pause":
                    settings["paused"] = not settings["paused"]

                elif data["action"] == "interrupt":
                    settings["interrupted"] = True
                    settings["paused"] = False

                elif data["action"] == "reset":
                    settings["paused"] = False
                    settings["interrupted"] = False
                    settings["reset"] = True

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            self.wfile.write(
                json.dumps({"status": "success", "state": settings}).encode()
            )
        else:
            self.send_response(404)
            self.end_headers()

    def get_html_content(self: "Server") -> str:
        build_dir = Path(__file__).parent.parent / "playground" / "build"

        html = (build_dir / "index.html").read_text()
        js = (build_dir / "script.js").read_text()
        css = (build_dir / "style.css").read_text()

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
        {css}
        </style>
        </head>
        <body>
        {html}
        <script>
        {js}
        </script>
        </body>
        </html>
        """
