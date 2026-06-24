#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import re
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse


REFRESH_SECONDS = 5
STATUS_PRIORITY = {
    "blocked": 0,
    "working": 1,
    "unknown": 2,
    "idle": 3,
    "done": 4,
}
ANSI_RE = re.compile(r"\x1b\[([0-9;]*)m")
ANSI_CSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
ANSI_16_COLORS = {
    30: "#0f1115",
    31: "#ff8f70",
    32: "#58c4a3",
    33: "#c6a76d",
    34: "#86a7ff",
    35: "#d59bf6",
    36: "#79d7e7",
    37: "#eef2f4",
    90: "#6f7881",
    91: "#ffb19d",
    92: "#7ad9bd",
    93: "#e0c781",
    94: "#a5baff",
    95: "#e1b0ff",
    96: "#9de6f2",
    97: "#ffffff",
}


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


def run_text(argv: list[str], timeout: float = 2.5) -> tuple[str | None, str | None]:
    try:
        completed = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as exc:
        return None, str(exc)

    if completed.returncode != 0:
        err = completed.stderr.strip() or completed.stdout.strip()
        return None, err or f"command exited {completed.returncode}"

    return completed.stdout, None


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


def status_priority(status: str) -> int:
    return STATUS_PRIORITY.get(status, STATUS_PRIORITY["unknown"])


def int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def session_priority(session: dict[str, Any]) -> tuple[int, str]:
    if not session.get("running"):
        return 5, str(session.get("name") or "")

    statuses = [
        str(agent.get("agent_status") or "unknown")
        for agent in session.get("agents", [])
    ]
    statuses.extend(
        str(workspace.get("agent_status") or "unknown")
        for workspace in session.get("workspaces", [])
    )

    if not statuses:
        return status_priority("unknown"), str(session.get("name") or "")

    return min(status_priority(status) for status in statuses), str(session.get("name") or "")


def agent_priority(agent: dict[str, Any]) -> tuple[int, str]:
    status = str(agent.get("agent_status") or "unknown")
    label = str(agent.get("agent") or agent.get("terminal_id") or "")
    return status_priority(status), label


def terminal_url(base_url: str, session: str, agent: str | None = None) -> str:
    args = ["--session", session]
    if agent:
        args.extend(["--agent", agent])
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{urlencode([('arg', arg) for arg in args])}"


def history_url(session: str, pane: str, lines: int = 400) -> str:
    base_url = os.environ.get("HERDR_STATUS_HISTORY_URL", "/history").strip() or "/history"
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{urlencode({'session': session, 'pane': pane, 'lines': str(lines)})}"


def ansi_256_color(index: int) -> str:
    if index < 16:
        base = [
            "#000000",
            "#800000",
            "#008000",
            "#808000",
            "#000080",
            "#800080",
            "#008080",
            "#c0c0c0",
            "#808080",
            "#ff0000",
            "#00ff00",
            "#ffff00",
            "#0000ff",
            "#ff00ff",
            "#00ffff",
            "#ffffff",
        ]
        return base[index]
    if 16 <= index <= 231:
        value = index - 16
        r = value // 36
        g = (value % 36) // 6
        b = value % 6
        scale = [0, 95, 135, 175, 215, 255]
        return f"#{scale[r]:02x}{scale[g]:02x}{scale[b]:02x}"
    gray = 8 + (index - 232) * 10
    return f"#{gray:02x}{gray:02x}{gray:02x}"


def style_attr(state: dict[str, str | bool]) -> str:
    parts = []
    if state.get("fg"):
        parts.append(f"color:{state['fg']}")
    if state.get("bg"):
        parts.append(f"background-color:{state['bg']}")
    if state.get("bold"):
        parts.append("font-weight:700")
    if state.get("dim"):
        parts.append("opacity:.72")
    if state.get("italic"):
        parts.append("font-style:italic")
    if state.get("underline"):
        parts.append("text-decoration:underline")
    return ";".join(parts)


def update_ansi_state(state: dict[str, str | bool], codes: list[int]) -> None:
    if not codes:
        codes = [0]
    i = 0
    while i < len(codes):
        code = codes[i]
        if code == 0:
            state.clear()
        elif code == 1:
            state["bold"] = True
        elif code == 2:
            state["dim"] = True
        elif code == 3:
            state["italic"] = True
        elif code == 4:
            state["underline"] = True
        elif code == 22:
            state.pop("bold", None)
            state.pop("dim", None)
        elif code == 23:
            state.pop("italic", None)
        elif code == 24:
            state.pop("underline", None)
        elif code == 39:
            state.pop("fg", None)
        elif code == 49:
            state.pop("bg", None)
        elif code in ANSI_16_COLORS:
            state["fg"] = ANSI_16_COLORS[code]
        elif 40 <= code <= 47:
            state["bg"] = ANSI_16_COLORS[code - 10]
        elif 100 <= code <= 107:
            state["bg"] = ANSI_16_COLORS[code - 10]
        elif code in {38, 48} and i + 2 < len(codes):
            target = "fg" if code == 38 else "bg"
            mode = codes[i + 1]
            if mode == 5 and i + 2 < len(codes):
                state[target] = ansi_256_color(codes[i + 2])
                i += 2
            elif mode == 2 and i + 4 < len(codes):
                r, g, b = codes[i + 2], codes[i + 3], codes[i + 4]
                state[target] = f"#{r:02x}{g:02x}{b:02x}"
                i += 4
        i += 1


def ansi_to_html(text: str) -> str:
    rendered = []
    state: dict[str, str | bool] = {}
    open_style = ""
    pos = 0

    def sync_span() -> None:
        nonlocal open_style
        next_style = style_attr(state)
        if next_style == open_style:
            return
        if open_style:
            rendered.append("</span>")
        if next_style:
            rendered.append(f'<span style="{html.escape(next_style, quote=True)}">')
        open_style = next_style

    def render_text_segment(segment: str) -> str:
        return html.escape(ANSI_CSI_RE.sub("", segment))

    for match in ANSI_RE.finditer(text):
        rendered.append(render_text_segment(text[pos : match.start()]))
        codes = [int(part) for part in match.group(1).split(";") if part != ""]
        update_ansi_state(state, codes)
        sync_span()
        pos = match.end()

    rendered.append(render_text_segment(text[pos:]))
    if open_style:
        rendered.append("</span>")

    return "".join(rendered)


def terminal_link_attrs(desktop_url: str, mobile_url: str) -> str:
    attrs = ""
    if desktop_url:
        attrs += f" data-desktop-url='{html.escape(desktop_url, quote=True)}'"
    if mobile_url:
        attrs += f" data-mobile-url='{html.escape(mobile_url, quote=True)}'"
    return attrs


def copy_button(url: str) -> str:
    if not url:
        return ""
    return (
        "<button class='copy-link' type='button' "
        f"data-copy-url='{html.escape(url, quote=True)}' "
        "aria-label='Copy terminal link'>Link</button>"
    )


def render_html(doc: dict[str, Any]) -> bytes:
    ttyd_url = os.environ.get("HERDR_STATUS_TTYD_URL", "").strip()
    ttyd_mobile_url = os.environ.get("HERDR_STATUS_TTYD_MOBILE_URL", "").strip()
    ttyd_desktop_url = os.environ.get("HERDR_STATUS_TTYD_DESKTOP_URL", "").strip() or ttyd_url
    ttyd_mobile_width = int_env("HERDR_STATUS_TTYD_MOBILE_WIDTH", 700)
    counts = status_counts(doc["sessions"])
    summary = " ".join(
        f"<span class='pill {html.escape(key)}'>{html.escape(key)} {value}</span>"
        for key, value in sorted(counts.items())
    ) or "<span class='muted'>No agents</span>"

    session_cards = []
    for session in sorted(doc["sessions"], key=session_priority):
        name = html.escape(str(session["name"]))
        running = bool(session["running"])
        agents = session.get("agents", [])
        workspaces = session.get("workspaces", [])
        errors = session.get("errors", [])
        session_url = terminal_url(ttyd_url, str(session["name"])) if ttyd_url else ""
        session_desktop_url = terminal_url(ttyd_desktop_url, str(session["name"])) if ttyd_desktop_url else session_url
        session_mobile_url = terminal_url(ttyd_mobile_url, str(session["name"])) if ttyd_mobile_url else ""
        session_attrs = terminal_link_attrs(session_desktop_url, session_mobile_url)
        session_link = (
            f"<a class='terminal-link' href='{html.escape(session_url)}'{session_attrs}>Session</a>"
            if session_url
            else ""
        )
        session_copy = copy_button(session_url)

        rows = []
        if agents:
            for agent in sorted(agents, key=agent_priority):
                agent_name = html.escape(str(agent.get("agent") or "terminal"))
                status = html.escape(str(agent.get("agent_status") or "unknown"))
                cwd = html.escape(str(agent.get("foreground_cwd") or agent.get("cwd") or ""))
                target = str(agent.get("terminal_id") or agent.get("agent") or "")
                pane_id = str(agent.get("pane_id") or "")
                location = html.escape(
                    f"{agent.get('workspace_id', '?')} / {agent.get('tab_id', '?')} / {agent.get('pane_id', '?')}"
                )
                focus = " focused" if agent.get("focused") else ""
                agent_url = terminal_url(ttyd_url, str(session["name"]), target) if ttyd_url and target else ""
                agent_desktop_url = terminal_url(ttyd_desktop_url, str(session["name"]), target) if ttyd_desktop_url and target else agent_url
                agent_mobile_url = terminal_url(ttyd_mobile_url, str(session["name"]), target) if ttyd_mobile_url and target else ""
                agent_attrs = terminal_link_attrs(agent_desktop_url, agent_mobile_url)
                agent_link = (
                    f"<a class='terminal-link compact' href='{html.escape(agent_url)}'{agent_attrs}>Agent</a>"
                    if agent_url
                    else ""
                )
                history_link = (
                    f"<a class='terminal-link compact secondary' href='{html.escape(history_url(str(session['name']), pane_id))}'>History</a>"
                    if pane_id
                    else ""
                )
                agent_copy = copy_button(agent_url)
                rows.append(
                    "<div class='agent-row'>"
                    f"<div class='agent-main'><strong>{agent_name}</strong>"
                    f"<span class='agent-actions'><span class='{status_class(status)}'>{status}</span>{agent_link}{history_link}{agent_copy}</span></div>"
                    f"<div class='cwd'>{cwd}</div>"
                    f"<div class='location{focus}'>{location}</div>"
                    "</div>"
                )
        else:
            rows.append("<div class='empty'>No agents in this session.</div>")

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
            f"<div class='card-head'><h2>{name}</h2><span class='agent-actions'>{session_link}{session_copy}"
            f"<span class='session-state {'running' if running else 'stopped'}'>{'running' if running else 'stopped'}</span></span></div>"
            f"<div class='workspaces'>{workspace_line or 'No workspaces'}</div>"
            f"{''.join(rows)}"
            f"{error_html}"
            "</section>"
        )

    terminal_link = (
        f"<a class='terminal-link' href='{html.escape(ttyd_url)}'{terminal_link_attrs(ttyd_desktop_url, ttyd_mobile_url)}>Default</a>"
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
    .agent-main {{ display: flex; align-items: center; gap: 10px; justify-content: space-between; }}
    .agent-actions {{ display: inline-flex; align-items: center; justify-content: flex-end; gap: 8px; flex-wrap: wrap; }}
    .cwd {{ margin-top: 6px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; overflow-wrap: anywhere; }}
    .location {{ margin-top: 4px; font-size: 12px; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    .location.focused::after {{ content: " focused"; color: var(--working); }}
    .status, .session-state, .pill {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      height: 28px;
      padding: 0 10px;
      border-radius: 999px;
      font-size: 12px;
      line-height: 1;
      border: 1px solid var(--line);
      background: #15181c;
      white-space: nowrap;
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
      display: inline-flex;
      align-items: center;
      justify-content: center;
      height: 32px;
      min-width: 64px;
      color: var(--text);
      text-decoration: none;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 12px;
      background: var(--panel-2);
      font-size: 13px;
      font-weight: 600;
      line-height: 1;
      white-space: nowrap;
    }}
    .terminal-link.compact {{ height: 28px; min-width: 62px; padding: 0 10px; font-size: 12px; }}
    .terminal-link.secondary {{ color: var(--muted); background: transparent; }}
    .copy-link {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      height: 28px;
      min-width: 54px;
      color: var(--muted);
      background: transparent;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 10px;
      font: inherit;
      font-size: 12px;
      line-height: 1;
      white-space: nowrap;
    }}
    .copy-link.copied {{ color: var(--working); border-color: rgba(88, 196, 163, 0.6); }}
    @media (max-width: 520px) {{
      .card-head {{ align-items: flex-start; flex-direction: column; }}
      .card-head .agent-actions {{ justify-content: flex-start; }}
      .agent-main {{ align-items: flex-start; flex-direction: column; }}
      .agent-actions {{ justify-content: flex-start; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Herdr Status</h1>
    <div class="meta">
      <span>{html.escape(doc["generated_at_iso"])}</span>
      <span>{REFRESH_SECONDS}s refresh</span>
      <span>{summary}</span>
      {terminal_link}
    </div>
  </header>
  <main>
    {''.join(session_cards)}
  </main>
  <script>
    const mobileTerminalWidth = {ttyd_mobile_width};

    function isMobileTerminalLayout() {{
      return window.matchMedia(`(max-width: ${{mobileTerminalWidth}}px)`).matches;
    }}

    function resolveTerminalUrl(element) {{
      const mobileUrl = element.dataset.mobileUrl;
      const desktopUrl = element.dataset.desktopUrl;
      const fallbackUrl = element.dataset.copyUrl || element.getAttribute("href") || "";
      const selectedUrl = isMobileTerminalLayout() && mobileUrl ? mobileUrl : desktopUrl || fallbackUrl;
      return new URL(selectedUrl, window.location.href).toString();
    }}

    function applyTerminalUrls() {{
      document.querySelectorAll("[data-desktop-url], [data-mobile-url]").forEach((link) => {{
        link.href = resolveTerminalUrl(link);
      }});
      document.querySelectorAll("[data-copy-url]").forEach((button) => {{
        const link = button.closest(".agent-actions, .meta")?.querySelector("[data-desktop-url], [data-mobile-url]");
        if (link) button.dataset.copyUrl = resolveTerminalUrl(link);
      }});
    }}

    applyTerminalUrls();
    window.addEventListener("resize", applyTerminalUrls);

    document.addEventListener("click", async (event) => {{
      const button = event.target.closest("[data-copy-url]");
      if (!button) return;
      applyTerminalUrls();
      const url = new URL(button.dataset.copyUrl, window.location.href).toString();
      try {{
        await navigator.clipboard.writeText(url);
        button.textContent = "Done";
        button.classList.add("copied");
        window.setTimeout(() => {{
          button.textContent = "Link";
          button.classList.remove("copied");
        }}, 1200);
      }} catch (error) {{
        window.prompt("Copy terminal link", url);
      }}
    }});
  </script>
</body>
</html>"""
    return body.encode("utf-8")


def render_history_html(session: str, pane: str, lines: int) -> bytes:
    output, err = run_text(
        [
            "herdr",
            "--session",
            session,
            "pane",
            "read",
            pane,
            "--source",
            "recent",
            "--lines",
            str(lines),
            "--format",
            "ansi",
        ],
        timeout=4,
    )
    content = output if output is not None else f"Error reading pane history: {err}"
    rendered_content = ansi_to_html(content)
    body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Herdr History</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #101214;
      --panel: #181b1f;
      --text: #eef2f4;
      --muted: #9aa4ad;
      --line: #313841;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    header {{
      position: sticky;
      top: 0;
      z-index: 1;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px;
      background: rgba(16, 18, 20, 0.96);
      border-bottom: 1px solid var(--line);
    }}
    .pull-indicator {{
      position: sticky;
      top: 0;
      z-index: 2;
      display: none;
      padding: 8px 12px;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
      text-align: center;
    }}
    .pull-indicator.visible {{ display: block; }}
    .pull-indicator.ready {{ color: var(--text); }}
    .history-actions {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }}
    h1 {{ margin: 0; font-size: 16px; letter-spacing: 0; }}
    .meta {{ color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }}
    a, button {{
      color: var(--text);
      background: transparent;
      text-decoration: none;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 7px 10px;
      font-size: 13px;
      white-space: nowrap;
      font-family: inherit;
    }}
    main {{ padding: 12px; }}
    .terminal-output {{
      margin: 0;
      padding: 12px;
      min-height: calc(100vh - 72px);
      overflow-x: auto;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      font: 12px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Pane History</h1>
      <div class="meta">{html.escape(session)} / {html.escape(pane)} / last {lines} lines / pull down for more</div>
    </div>
    <div class="history-actions">
      <button type="button" id="load-more">More</button>
      <button type="button" id="refresh-now">Refresh</button>
      <a href="/">Status</a>
    </div>
  </header>
  <div id="pull-indicator" class="pull-indicator">Pull down for more history</div>
  <main>
    <div class="terminal-output">{rendered_content}</div>
  </main>
  <script>
    const loadMore = document.getElementById("load-more");
    const refreshNow = document.getElementById("refresh-now");
    const pullIndicator = document.getElementById("pull-indicator");
    let touchStartY = null;
    let pullDistance = 0;
    const refreshThreshold = 90;
    const currentLines = {lines};
    const maxLines = 2000;
    const lineStep = 400;

    if (currentLines >= maxLines) {{
      loadMore.disabled = true;
      loadMore.textContent = "All";
    }}

    function refreshHistory() {{
      window.location.reload();
    }}

    function loadMoreHistory() {{
      const nextLines = Math.min(currentLines + lineStep, maxLines);
      if (nextLines === currentLines) {{
        pullIndicator.textContent = "All retained history is loaded";
        window.setTimeout(() => {{
          pullIndicator.classList.remove("visible", "ready");
          pullIndicator.textContent = "Pull down for more history";
        }}, 1000);
        return;
      }}
      const url = new URL(window.location.href);
      url.searchParams.set("lines", String(nextLines));
      url.searchParams.set("anchor", "top");
      window.location.href = url.toString();
    }}

    loadMore.addEventListener("click", loadMoreHistory);
    refreshNow.addEventListener("click", refreshHistory);
    window.addEventListener("load", () => {{
      const params = new URLSearchParams(window.location.search);
      if (params.get("anchor") === "top") {{
        window.scrollTo(0, 0);
      }} else {{
        window.scrollTo(0, document.documentElement.scrollHeight);
      }}
    }});

    window.addEventListener("touchstart", (event) => {{
      if (window.scrollY === 0 && event.touches.length === 1) {{
        touchStartY = event.touches[0].clientY;
        pullDistance = 0;
      }}
    }}, {{ passive: true }});

    window.addEventListener("touchmove", (event) => {{
      if (touchStartY === null || event.touches.length !== 1) return;
      pullDistance = event.touches[0].clientY - touchStartY;
      if (pullDistance <= 20) return;
      pullIndicator.classList.add("visible");
      if (pullDistance >= refreshThreshold) {{
        pullIndicator.textContent = currentLines >= maxLines ? "All retained history is loaded" : "Release to load more";
        pullIndicator.classList.add("ready");
      }} else {{
        pullIndicator.textContent = "Pull down for more history";
        pullIndicator.classList.remove("ready");
      }}
    }}, {{ passive: true }});

    window.addEventListener("touchend", () => {{
      if (touchStartY !== null && pullDistance >= refreshThreshold) {{
        pullIndicator.textContent = "Loading more...";
        loadMoreHistory();
        return;
      }}
      touchStartY = null;
      pullDistance = 0;
      pullIndicator.classList.remove("visible", "ready");
      pullIndicator.textContent = "Pull down for more history";
    }});
  </script>
</body>
</html>"""
    return body.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            doc = collect_status()
            body = render_html(doc)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/history":
            params = parse_qs(parsed.query)
            session = params.get("session", [""])[0]
            pane = params.get("pane", [""])[0]
            try:
                lines = min(max(int(params.get("lines", ["400"])[0]), 20), 2000)
            except ValueError:
                lines = 400

            if not session or not pane:
                self.send_error(400, "missing session or pane")
                return

            body = render_history_html(session, pane, lines)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/api.json":
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
