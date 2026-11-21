# Paseo

Paseo is installed from the official Debian package. The package includes the
desktop application, CLI, and headless daemon.

## Local installation

- Package: `paseo` 0.16.1
- CLI: `@getpaseo/cli` 0.16.1, installed by mise
- Daemon home: `~/.paseo`
- Listen address: `127.0.0.1:6767`
- User service: `paseo-daemon.service`

The daemon is kept local by default. Enable the user service after installing
the package:

```bash
mkdir -p ~/.config/systemd/user
cp dev/dev-machine/paseo/systemd/paseo-daemon.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now paseo-daemon.service
```

Verify the installation:

```bash
paseo --version
paseo daemon status --json
systemctl --user status paseo-daemon.service --no-pager
```

The desktop application requires a graphical session. Headless use should use
the CLI and daemon service.
