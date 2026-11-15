#!/usr/bin/env bash
# HC-AI | ticket: FDD-TOOL-CODEMAP
# Build the site locally and upload it to a VPS that runs nginx.
#
#   DEPLOY_HOST=deploy@203.0.113.10 DOMAIN=cbm.example.com website/deploy/deploy.sh --setup
#   DEPLOY_HOST=deploy@203.0.113.10 DOMAIN=cbm.example.com website/deploy/deploy.sh
#
# --setup (first run only) installs the nginx site, creates the web root and
# reloads nginx; it needs sudo on the VPS. It will not replace an existing site
# config, because certbot adds the HTTPS server to that file; FORCE=1 replaces
# it anyway. Later runs only rebuild and rsync, and only into a web root that
# --setup created (it holds the marker file below).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEBSITE="$(dirname "$HERE")"
PYTHON="${PYTHON:-python3}"
WEBROOT="${WEBROOT:-/var/www/codebase-map}"
MARKER=".codebase-map-webroot"
SITE_CONF="/etc/nginx/sites-available/codebase-map"
SITE_LINK="/etc/nginx/sites-enabled/codebase-map"
: "${DEPLOY_HOST:?set DEPLOY_HOST=user@host}"
: "${DOMAIN:?set DOMAIN=your.domain}"
force=0
[[ "${FORCE:-}" == 1 ]] && force=1

die() {
  echo "$*" >&2
  exit 1
}

[[ "$DOMAIN" =~ ^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$ ]] || die "DOMAIN looks wrong: $DOMAIN"
# user@host or an ssh config alias, never something ssh would read as an option.
[[ "$DEPLOY_HOST" =~ ^([A-Za-z0-9_][A-Za-z0-9._-]*@)?[A-Za-z0-9][A-Za-z0-9.-]*$ ]] ||
  die "DEPLOY_HOST looks wrong (expected user@host or an ssh alias): $DEPLOY_HOST"
# Exactly one folder under /var/www or /srv, so rsync --delete cannot reach
# anything else on the server.
[[ "$WEBROOT" =~ ^/(var/www|srv)/[A-Za-z0-9_-][A-Za-z0-9._-]*$ ]] ||
  die "WEBROOT must be one folder directly under /var/www or /srv: $WEBROOT"

# The demo map shows the branch and commit it was built from.
repo="$(dirname "$WEBSITE")"
branch="$(git -C "$repo" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")"
if [[ "$branch" != main ]] || [[ -n "$(git -C "$repo" status --porcelain 2>/dev/null)" ]]; then
  echo "Warning: this is not a clean checkout of main (branch '$branch')." \
    "The public demo will show this branch and commit." >&2
fi

"$PYTHON" "$WEBSITE/build.py" --site-url "https://$DOMAIN"

if [[ "${1:-}" == "--setup" ]]; then
  conf="$(mktemp)"
  trap 'rm -f "$conf"' EXIT
  sed -e "s/cbm\.example\.com/$DOMAIN/g" -e "s#/var/www/codebase-map#$WEBROOT#g" \
    "$HERE/nginx.conf" > "$conf"
  # Upload to the SSH user's home, not a fixed path in the shared /tmp.
  scp "$conf" "$DEPLOY_HOST:codebase-map.nginx"
  ssh -t "$DEPLOY_HOST" "set -eu
    upload=\"\$HOME/codebase-map.nginx\"
    trap 'rm -f \"\$upload\"' EXIT
    if [ -e '$SITE_CONF' ] && [ $force != 1 ]; then
      echo '$SITE_CONF already exists (certbot may have added HTTPS to it).' >&2
      echo 'Nothing changed. Run with FORCE=1 to replace it, then run certbot again.' >&2
      exit 1
    fi
    # sudo, so a folder the SSH user cannot read is never mistaken for empty.
    if sudo test -e '$WEBROOT' && ! sudo test -e '$WEBROOT/$MARKER' &&
      [ -n \"\$(sudo find '$WEBROOT' -mindepth 1 -print -quit)\" ]; then
      echo '$WEBROOT already has files and was not created by this script. Pick another WEBROOT.' >&2
      exit 1
    fi
    # Web root first: if it cannot be created, nginx is not touched at all.
    sudo mkdir -p '$WEBROOT'
    sudo chown \"\$(id -un)\" '$WEBROOT'
    touch '$WEBROOT/$MARKER'
    sudo rm -f '$SITE_CONF.bak'
    if [ -e '$SITE_CONF' ]; then sudo cp '$SITE_CONF' '$SITE_CONF.bak'; fi
    sudo install -m 644 \"\$upload\" '$SITE_CONF'
    sudo ln -sf '$SITE_CONF' '$SITE_LINK'
    if ! sudo nginx -t; then
      if [ -e '$SITE_CONF.bak' ]; then
        sudo mv '$SITE_CONF.bak' '$SITE_CONF'
      else
        sudo rm -f '$SITE_LINK' '$SITE_CONF'
      fi
      echo 'nginx -t failed: the previous state was restored and nginx was not reloaded.' >&2
      exit 1
    fi
    sudo systemctl reload nginx"
fi

ssh "$DEPLOY_HOST" "test -f '$WEBROOT/$MARKER'" ||
  die "$WEBROOT on $DEPLOY_HOST was not set up by this script (no $MARKER). Run with --setup first."
# The marker is excluded, so --delete never removes it.
rsync -az --delete --exclude="/$MARKER" "$WEBSITE/dist/" "$DEPLOY_HOST:$WEBROOT/"
echo "Deployed to http://$DOMAIN (files in $DEPLOY_HOST:$WEBROOT)"
if [[ "${1:-}" == "--setup" ]]; then
  echo "Next, for HTTPS: ssh $DEPLOY_HOST 'sudo certbot --nginx -d $DOMAIN'"
fi
