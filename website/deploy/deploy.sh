#!/usr/bin/env bash
# HC-AI | ticket: FDD-TOOL-CODEMAP
# Build the site locally and upload it to a VPS that runs nginx.
#
#   DEPLOY_HOST=deploy@203.0.113.10 DOMAIN=cbm.example.com website/deploy/deploy.sh --setup
#   DEPLOY_HOST=deploy@203.0.113.10 DOMAIN=cbm.example.com website/deploy/deploy.sh
#
# --setup (first run only) installs the nginx site, creates the web root and
# reloads nginx; it needs sudo on the VPS. Later runs only rebuild and rsync.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEBSITE="$(dirname "$HERE")"
PYTHON="${PYTHON:-python3}"
WEBROOT="${WEBROOT:-/var/www/codebase-map}"
: "${DEPLOY_HOST:?set DEPLOY_HOST=user@host}"
: "${DOMAIN:?set DOMAIN=your.domain}"

[[ "$DOMAIN" =~ ^[A-Za-z0-9.-]+$ ]] || { echo "DOMAIN looks wrong: $DOMAIN" >&2; exit 1; }
[[ "$WEBROOT" =~ ^/[A-Za-z0-9._/-]+$ ]] || { echo "WEBROOT looks wrong: $WEBROOT" >&2; exit 1; }

"$PYTHON" "$WEBSITE/build.py" --site-url "https://$DOMAIN"

if [[ "${1:-}" == "--setup" ]]; then
  conf="$(mktemp)"
  trap 'rm -f "$conf"' EXIT
  sed -e "s/cbm\.example\.com/$DOMAIN/g" -e "s#/var/www/codebase-map#$WEBROOT#g" \
    "$HERE/nginx.conf" > "$conf"
  scp "$conf" "$DEPLOY_HOST:/tmp/codebase-map.nginx"
  ssh -t "$DEPLOY_HOST" "set -e
    sudo install -m 644 /tmp/codebase-map.nginx /etc/nginx/sites-available/codebase-map
    rm -f /tmp/codebase-map.nginx
    sudo ln -sf /etc/nginx/sites-available/codebase-map /etc/nginx/sites-enabled/codebase-map
    sudo mkdir -p '$WEBROOT'
    sudo chown \"\$(id -un)\" '$WEBROOT'
    sudo nginx -t
    sudo systemctl reload nginx"
fi

rsync -az --delete "$WEBSITE/dist/" "$DEPLOY_HOST:$WEBROOT/"
echo "Deployed to http://$DOMAIN (files in $DEPLOY_HOST:$WEBROOT)"
if [[ "${1:-}" == "--setup" ]]; then
  echo "Next, for HTTPS: ssh $DEPLOY_HOST 'sudo certbot --nginx -d $DOMAIN'"
fi
