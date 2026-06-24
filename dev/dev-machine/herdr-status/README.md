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
HERDR_STATUS_TTYD_URL=/terminal/
```

`HERDR_STATUS_TTYD_URL` is optional. When set, the page shows an "Open terminal"
link. With the `herdr-web` Caddy router, keep it as `/terminal/` so the link
works under whichever ngrok URL is currently active.

The dashboard also generates per-session and per-agent terminal links:

```text
/terminal/?arg=--session&arg=default
/terminal/?arg=--session&arg=default&arg=--agent&arg=term_...
```

Those arguments are handled by `herdr-web-session`, which accepts only
`--session` and `--agent`.

## Browser Routes

When installed with `herdr-web`, Caddy exposes these local routes on
`127.0.0.1:8780` and ngrok forwards the same paths:

```text
/           status dashboard
/api.json   raw status JSON
/terminal/  ttyd terminal
```

## Scope

The service is read-only. It does not send input to panes, start agents, stop
sessions, or expose shell access.
