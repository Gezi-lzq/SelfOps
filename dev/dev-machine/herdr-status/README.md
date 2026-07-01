# Herdr Status

Read-only mobile dashboard for Herdr sessions and agents.

This is not a terminal replacement. It exists so a phone can quickly answer:

- Which Herdr sessions are running?
- Which agents are `working`, `blocked`, `done`, `idle`, or `unknown`?
- Which workspace/tab/pane and cwd is each agent in?

## Run Locally

```bash
mise run herdr-status:serve
```

Then open:

```text
http://127.0.0.1:8765/
http://127.0.0.1:8765/api.json
```

## Configuration

Environment variables:

```text
HERDR_STATUS_HOST=127.0.0.1
HERDR_STATUS_PORT=8765
HERDR_STATUS_TTYD_URL=/herdr/terminal/
HERDR_STATUS_HISTORY_URL=/herdr/history
# Optional:
HERDR_STATUS_TTYD_DESKTOP_URL=/herdr/terminal/
HERDR_STATUS_TTYD_MOBILE_URL=/herdr/touch-terminal/
HERDR_STATUS_TTYD_MOBILE_WIDTH=700
```

`HERDR_STATUS_TTYD_URL` is optional. When set, the page shows a `Default`
link. With the `herdr-web` Caddy router, keep it under `/herdr/terminal/` so
the link works under whichever ngrok URL is currently active.

When `HERDR_STATUS_TTYD_MOBILE_URL` is set, terminal links are resolved in the
browser. Viewports at or below `HERDR_STATUS_TTYD_MOBILE_WIDTH` use the mobile
base URL, while wider screens use `HERDR_STATUS_TTYD_DESKTOP_URL`. The status
service appends the same ttyd `arg=...` parameters after choosing the base URL.
Use `/herdr/touch-terminal/` as the mobile URL so phone links get the touch
controls and view-mode input guard.

The dashboard also generates per-session and per-agent terminal links:

```text
/herdr/terminal/?arg=--session&arg=default
/herdr/terminal/?arg=--session&arg=default&arg=--agent&arg=term_...
```

Those arguments are handled by `herdr-web-session`, which accepts only
`--session` and `--agent`.

Each detected agent also has a `History` link:

```text
/history?session=default&pane=w1:p1&lines=400
```

This renders recent pane output as a normal scrollable HTML page while preserving
ANSI colors and emphasis. It is useful on mobile browsers where the
ttyd/xterm.js full-screen terminal may not expose touch scrolling over Herdr's
pane history.

Sessions and agents are sorted by attention priority:

```text
blocked > working > unknown > idle > done > stopped
```

Each generated terminal link has a `Link` button that copies the absolute URL
for use on another device.

## Browser Routes

When installed with `herdr-web`, Caddy exposes these local routes on
`127.0.0.1:8780` and ngrok forwards the same paths:

```text
/           gezi-dev service homepage
/herdr      status dashboard entry
/herdr/api.json   raw status JSON
/herdr/history    read-only scrollable pane history
/herdr/terminal/  ttyd terminal
/herdr/terminal-mobile/  ttyd terminal with larger mobile font
/herdr/touch-terminal/  mobile ttyd wrapper with touch controls
```

Only `/herdr` is intended as a homepage entry. The other paths are service
subroutes used by the Herdr dashboard and ttyd.

## Scope

The service is read-only. It does not send input to panes, start agents, stop
sessions, or expose shell access.
