# Herdr Web Access

Expose a Herdr session through a browser using:

- `ttyd`: local web terminal bound to `127.0.0.1`
- `herdr-status`: read-only mobile dashboard for sessions and agents
- `caddy`: local path router
- `ngrok`: public tunnel to the local router
- `cloudflared`: optional quick tunnel fallback when ngrok endpoint pooling is not stable
- `systemd --user`: keeps both processes running for the `debian` user

This module is for temporary or personal browser access to the current dev
machine. It must not store ngrok tokens or web terminal passwords in Git.

## Security Model

The local services bind to localhost only:

```text
127.0.0.1:7681  ttyd
127.0.0.1:8765  status dashboard
127.0.0.1:8780  caddy router
```

Only ngrok exposes the Caddy router publicly. By default ttyd requires HTTP
basic auth through `HERDR_WEB_TTYD_CREDENTIAL`.

The credential lives in:

```text
~/.config/selfops/herdr-web.env
```

Do not commit that file.

Operational note: ttyd receives basic auth through the `-c user:password`
argument, so the credential can be visible to local users through process
inspection. This is acceptable for a single-user dev machine, but if you enable
ngrok OAuth or another edge access-control layer, clear
`HERDR_WEB_TTYD_CREDENTIAL` and let the tunnel handle authentication.

## Requirements

- `herdr`
- `ttyd`
- `caddy`
- `ngrok` or `cloudflared`
- `systemd --user`

ngrok must already be authenticated:

```bash
ngrok config add-authtoken <token>
```

Install ngrok with either the official installer/package repository, or this
repo's user-local helper:

```bash
mise run herdr-web:install-ngrok
```

That helper installs `ngrok` to `~/.local/bin/ngrok`.

## Install

From the SelfOps repo root:

```bash
mise run herdr-web:install
```

The installer creates:

```text
~/.config/selfops/herdr-web.env
~/.config/selfops/herdr-status.env
~/.config/systemd/user/herdr-web-ttyd.service
~/.config/systemd/user/herdr-status.service
~/.config/systemd/user/herdr-web-proxy.service
~/.config/systemd/user/herdr-web-ngrok.service
~/.config/systemd/user/herdr-web-cloudflared.service
```

Edit the env file if needed:

```bash
$EDITOR ~/.config/selfops/herdr-web.env
```

If ngrok fails with `ERR_NGROK_334`, the selected account endpoint is already
online elsewhere. Either stop that existing tunnel, configure a different
`HERDR_WEB_NGROK_URL`, or set:

```bash
HERDR_WEB_NGROK_POOLING=true
```

Pooling is only a fallback. If another backend behind the same ngrok endpoint is
misconfigured, requests may intermittently hit that backend instead of this
machine. In that case, stop the stale endpoint in ngrok or configure a different
static endpoint before disabling pooling again.

If you need an immediate stable public URL and do not require a fixed domain, use
the Cloudflare quick tunnel service instead of ngrok:

```bash
mise run herdr-web:start-cloudflared
mise run herdr-web:cloudflared-url
```

Quick tunnel URLs are temporary, but they point only to this machine and avoid
ngrok endpoint pooling.

## Start

```bash
mise run herdr-web:start
```

Show the ngrok browser URL:

```bash
mise run herdr-web:url
```

Show the Cloudflare quick tunnel URL:

```bash
mise run herdr-web:cloudflared-url
```

Routes on that URL:

```text
/           read-only Herdr status dashboard
/api.json   raw dashboard JSON
/terminal/  ttyd browser terminal
```

The status dashboard renders direct terminal links for each session and detected
agent. These links use ttyd URL arguments:

```text
/terminal/?arg=--session&arg=default
/terminal/?arg=--session&arg=default&arg=--agent&arg=term_...
```

The `herdr-web-session` wrapper intentionally accepts only `--session` and
`--agent`, then runs either `herdr --session <name>` or
`herdr --session <name> agent attach <target> --takeover`.

Follow logs:

```bash
mise run herdr-web:logs
```

Stop:

```bash
mise run herdr-web:stop
```

Enable on login:

```bash
mise run herdr-web:enable
```

## Default Browser Session

By default the browser opens:

```bash
herdr --session browser
```

Change the session name in:

```bash
~/.config/selfops/herdr-web.env
```

For advanced cases, set `HERDR_WEB_COMMAND` to override the command executed by
the browser terminal.
