#!/usr/bin/env bash
set -euo pipefail

remote="${DEV_MACHINE_SSH:-debian@gezi-dev.netbird.cloud}"

local_saml="${HOME}/.saml2aws"
local_aws_config="${HOME}/.aws/config"
local_aws_credentials="${HOME}/.aws/credentials"

for path in "$local_saml" "$local_aws_config" "$local_aws_credentials"; do
  if [[ ! -f "$path" ]]; then
    echo "missing required local file: $path" >&2
    exit 1
  fi
done

ts="$(date -u +%Y%m%dT%H%M%SZ)"
remote_tmp=".aws/.sync-aws-credentials-${ts}"
remote_backup=".aws/backups/aws-credentials-${ts}"

echo "syncing AWS credential files to ${remote}"

ssh "$remote" "set -e
umask 077
mkdir -p .aws/backups '${remote_tmp}'
mkdir -p '${remote_backup}/.aws'
if [ -f .saml2aws ]; then cp -p .saml2aws '${remote_backup}/.saml2aws'; fi
if [ -f .aws/config ]; then cp -p .aws/config '${remote_backup}/.aws/config'; fi
if [ -f .aws/credentials ]; then cp -p .aws/credentials '${remote_backup}/.aws/credentials'; fi"

rsync -a "$local_saml" "${remote}:${remote_tmp}/saml2aws"
rsync -a "$local_aws_config" "${remote}:${remote_tmp}/aws-config"
rsync -a "$local_aws_credentials" "${remote}:${remote_tmp}/aws-credentials"

ssh "$remote" "set -e
umask 077
mkdir -p .aws
install -m 600 '${remote_tmp}/saml2aws' .saml2aws
install -m 600 '${remote_tmp}/aws-config' .aws/config
install -m 600 '${remote_tmp}/aws-credentials' .aws/credentials
rm -rf '${remote_tmp}'"

echo "done"
echo "remote backup: ~/${remote_backup}"
