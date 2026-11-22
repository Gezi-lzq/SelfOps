# AWS credential sync

Repeatable local-to-`gezi-dev` sync for AWS CLI and `saml2aws` credential files.

This directory records the procedure only. Credential files are local secrets and
must not be committed.

## Files Synced

- `~/.saml2aws`
- `~/.aws/config`
- `~/.aws/credentials`

## Usage

From the local workstation:

```bash
./dev/dev-machine/aws-credentials/sync-to-gezi-dev.sh
```

Optional environment variables:

```bash
DEV_MACHINE_SSH=debian@gezi-dev.netbird.cloud ./dev/dev-machine/aws-credentials/sync-to-gezi-dev.sh
```

The script creates a timestamped backup of any existing remote files under:

```text
~/.aws/backups/aws-credentials-<timestamp>/
```

Remote file permissions are set to `600`.
