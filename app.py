from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from flask import Flask, render_template, request

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)


def run_command(command: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (completed.stdout or "")
    if completed.stderr:
        output += "\n" + completed.stderr
    return completed.returncode, output.strip()


def parse_inputs(form: dict[str, str]) -> tuple[float, float, int]:
    lat = float(form.get("lat", "44.4938"))
    lng = float(form.get("lng", "11.3426"))
    radius = int(form.get("radius", "2000"))
    return lat, lng, radius


@app.route("/", methods=["GET", "POST"])
def index():
    context = {
        "lat": "44.4938",
        "lng": "11.3426",
        "radius": "2000",
        "output": "",
        "error": "",
        "status": "Idle",
    }

    if request.method == "POST":
        context["lat"] = request.form.get("lat", context["lat"])
        context["lng"] = request.form.get("lng", context["lng"])
        context["radius"] = request.form.get("radius", context["radius"])
        action = request.form.get("action", "")

        try:
            lat, lng, radius = parse_inputs(request.form)
            commands: list[tuple[str, list[str]]] = []

            if action == "check":
                commands.append(("System Check", [sys.executable, "brain.py"]))
            elif action == "scout":
                commands.append(
                    (
                        "Scout Mission",
                        [sys.executable, "agent_scout.py", str(lat), str(lng)],
                    )
                )
            elif action == "critic":
                commands.append(("Critic Mission", [sys.executable, "agent_critic.py"]))
            elif action == "full":
                commands.append(
                    (
                        "Scout Mission",
                        [sys.executable, "agent_scout.py", str(lat), str(lng)],
                    )
                )
                commands.append(("Critic Mission", [sys.executable, "agent_critic.py"]))
            else:
                raise ValueError("Azione non valida.")

            logs: list[str] = []
            overall_ok = True

            for title, cmd in commands:
                rc, out = run_command(cmd)
                logs.append(f"$ {' '.join(cmd)}")
                logs.append(f"## {title}")
                logs.append(out or "(nessun output)")
                logs.append("-" * 60)
                if rc != 0:
                    overall_ok = False
                    logs.append(f"Interrotto: comando terminato con codice {rc}.")
                    break

            context["output"] = "\n".join(logs)
            context["status"] = "Completato" if overall_ok else "Errore"
        except Exception as exc:
            context["error"] = str(exc)
            context["status"] = "Errore"

    return render_template("index.html", **context)


if __name__ == "__main__":
    app.run(debug=True)
