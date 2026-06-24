# Herdr Web Access

Expose a Herdr session through a browser using:

- `ttyd`: local web terminal bound to `127.0.0.1`
- `ngrok`: public tunnel to the local ttyd port
- `systemd --user`: keeps both processes running for the `debian` user

This module is for temporary or personal browser access to the current dev
machine. It must not store ngrok tokens or web terminal passwords in Git.

## Security Model

The ttyd process binds to localhost only:

```text
127.0.0.1:7681
```

Only ngrok exposes it publicly. By default ttyd requires HTTP basic auth through
`HERDR_WEB_TTYD_CREDENTIAL`.

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
- `ngrok`
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
~/.config/systemd/user/herdr-web-ttyd.service
~/.config/systemd/user/herdr-web-ngrok.service
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

## Start

```bash
mise run herdr-web:start
```

Show the ngrok browser URL:

```bash
mise run herdr-web:url
```

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
