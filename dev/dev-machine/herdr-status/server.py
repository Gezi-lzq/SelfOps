#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


REFRESH_SECONDS = 5


def run_json(argv: list[str], timeout: float = 2.5) -> tuple[dict[str, Any] | None, str | None]:
    try:
        completed = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as exc:  # subprocess errors become dashboard diagnostics.
        return None, str(exc)

    if completed.returncode != 0:
        err = completed.stderr.strip() or completed.stdout.strip()
        return None, err or f"command exited {completed.returncode}"

    try:
        return json.loads(completed.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"invalid json: {exc}"


def collect_status() -> dict[str, Any]:
    now = int(time.time())
    sessions_doc, sessions_err = run_json(["herdr", "session", "list", "--json"])
    sessions = []

    if sessions_doc:
        for session in sessions_doc.get("sessions", []):
            name = session.get("name", "")
            entry: dict[str, Any] = {
                "name": name,
                "default": bool(session.get("default")),
                "running": bool(session.get("running")),
                "session_dir": session.get("session_dir"),
                "socket_path": session.get("socket_path"),
                "agents": [],
                "workspaces": [],
                "tabs": [],
                "errors": [],
            }

            if entry["running"] and name:
                agent_doc, agent_err = run_json(["herdr", "--session", name, "agent", "list"])
                if agent_doc:
                    entry["agents"] = agent_doc.get("result", {}).get("agents", [])
                elif agent_err:
                    entry["errors"].append({"source": "agent list", "message": agent_err})

                workspace_doc, workspace_err = run_json(["herdr", "--session", name, "workspace", "list"])
                if workspace_doc:
                    entry["workspaces"] = workspace_doc.get("result", {}).get("workspaces", [])
                elif workspace_err:
                    entry["errors"].append({"source": "workspace list", "message": workspace_err})

                tab_doc, tab_err = run_json(["herdr", "--session", name, "tab", "list"])
                if tab_doc:
                    entry["tabs"] = tab_doc.get("result", {}).get("tabs", [])
                elif tab_err:
                    entry["errors"].append({"source": "tab list", "message": tab_err})

            sessions.append(entry)

    return {
        "generated_at": now,
        "generated_at_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        "errors": [{"source": "session list", "message": sessions_err}] if sessions_err else [],
        "sessions": sessions,
    }


def status_counts(sessions: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for session in sessions:
        for agent in session.get("agents", []):
            status = str(agent.get("agent_status") or "unknown")
            counts[status] = counts.get(status, 0) + 1
    return counts


def status_class(status: str) -> str:
    if status in {"blocked", "unknown"}:
        return f"status {status}"
    if status in {"working", "done", "idle"}:
        return f"status {status}"
    return "status unknown"


def render_html(doc: dict[str, Any]) -> bytes:
    ttyd_url = os.environ.get("HERDR_STATUS_TTYD_URL", "").strip()
    counts = status_counts(doc["sessions"])
    summary = " ".join(
        f"<span class='pill {html.escape(key)}'>{html.escape(key)} {value}</span>"
        for key, value in sorted(counts.items())
    ) or "<span class='muted'>No agents detected</span>"

    session_cards = []
    for session in doc["sessions"]:
        name = html.escape(str(session["name"]))
        running = bool(session["running"])
        agents = session.get("agents", [])
        workspaces = session.get("workspaces", [])
        errors = session.get("errors", [])

        rows = []
        if agents:
            for agent in agents:
                agent_name = html.escape(str(agent.get("agent") or "terminal"))
                status = html.escape(str(agent.get("agent_status") or "unknown"))
                cwd = html.escape(str(agent.get("foreground_cwd") or agent.get("cwd") or ""))
                location = html.escape(
                    f"{agent.get('workspace_id', '?')} / {agent.get('tab_id', '?')} / {agent.get('pane_id', '?')}"
                )
                focus = " focused" if agent.get("focused") else ""
                rows.append(
                    "<div class='agent-row'>"
                    f"<div class='agent-main'><strong>{agent_name}</strong>"
                    f"<span class='{status_class(status)}'>{status}</span></div>"
                    f"<div class='cwd'>{cwd}</div>"
                    f"<div class='location{focus}'>{location}</div>"
                    "</div>"
                )
        else:
            rows.append("<div class='empty'>No agents detected in this session.</div>")

        workspace_line = ", ".join(
            html.escape(f"{w.get('label') or w.get('workspace_id')}:{w.get('agent_status', 'unknown')}")
            for w in workspaces
        )

        error_html = "".join(
            f"<div class='error'>{html.escape(e.get('source', 'error'))}: {html.escape(e.get('message', ''))}</div>"
            for e in errors
        )

        session_cards.append(
            "<section class='card'>"
            f"<div class='card-head'><h2>{name}</h2>"
            f"<span class='session-state {'running' if running else 'stopped'}'>{'running' if running else 'stopped'}</span></div>"
            f"<div class='workspaces'>{workspace_line or 'No workspace summary'}</div>"
            f"{''.join(rows)}"
            f"{error_html}"
            "</section>"
        )

    terminal_link = (
        f"<a class='terminal-link' href='{html.escape(ttyd_url)}'>Open terminal</a>"
        if ttyd_url
        else ""
    )

    body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="{REFRESH_SECONDS}">
  <title>Herdr Status</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #101214;
      --panel: #181b1f;
      --panel-2: #20242a;
      --text: #eef2f4;
      --muted: #9aa4ad;
      --line: #313841;
      --working: #58c4a3;
      --blocked: #ff8f70;
      --done: #86a7ff;
      --idle: #a7adb4;
      --unknown: #c6a76d;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.35;
    }}
    header {{
      position: sticky;
      top: 0;
      background: rgba(16, 18, 20, 0.96);
      border-bottom: 1px solid var(--line);
      padding: 14px 16px 12px;
      z-index: 1;
    }}
    h1 {{ margin: 0 0 8px; font-size: 20px; letter-spacing: 0; }}
    h2 {{ margin: 0; font-size: 17px; letter-spacing: 0; }}
    .meta, .workspaces, .cwd, .location, .empty, .muted {{ color: var(--muted); }}
    .meta {{ font-size: 13px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }}
    main {{ padding: 12px; display: grid; gap: 12px; max-width: 860px; margin: 0 auto; }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    .card-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      padding: 12px;
      background: var(--panel-2);
      border-bottom: 1px solid var(--line);
    }}
    .workspaces {{ padding: 10px 12px; font-size: 13px; border-bottom: 1px solid var(--line); }}
    .agent-row {{ padding: 12px; border-top: 1px solid var(--line); }}
    .agent-row:first-of-type {{ border-top: 0; }}
    .agent-main {{ display: flex; align-items: center; gap: 8px; justify-content: space-between; }}
    .cwd {{ margin-top: 6px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; overflow-wrap: anywhere; }}
    .location {{ margin-top: 4px; font-size: 12px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    .location.focused::after {{ content: " focused"; color: var(--working); }}
    .status, .session-state, .pill {{
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 3px 8px;
      border-radius: 999px;
      font-size: 12px;
      border: 1px solid var(--line);
      background: #15181c;
    }}
    .working {{ color: var(--working); }}
    .blocked {{ color: var(--blocked); }}
    .done {{ color: var(--done); }}
    .idle {{ color: var(--idle); }}
    .unknown {{ color: var(--unknown); }}
    .running {{ color: var(--working); }}
    .stopped {{ color: var(--idle); }}
    .error {{ padding: 10px 12px; color: var(--blocked); border-top: 1px solid var(--line); font-size: 13px; }}
    .empty {{ padding: 12px; }}
    .terminal-link {{
      color: var(--text);
      text-decoration: none;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 5px 8px;
      background: var(--panel-2);
    }}
  </style>
</head>
<body>
  <header>
    <h1>Herdr Status</h1>
    <div class="meta">
      <span>{html.escape(doc["generated_at_iso"])}</span>
      <span>refresh {REFRESH_SECONDS}s</span>
      <span>{summary}</span>
      {terminal_link}
    </div>
  </header>
  <main>
    {''.join(session_cards)}
  </main>
</body>
</html>"""
    return body.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            doc = collect_status()
            body = render_html(doc)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/api.json":
            body = json.dumps(collect_status(), indent=2, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404)

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def main() -> None:
    host = os.environ.get("HERDR_STATUS_HOST", "127.0.0.1")
    port = int(os.environ.get("HERDR_STATUS_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"herdr-status listening on http://{host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

