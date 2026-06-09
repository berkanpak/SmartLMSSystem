#!/usr/bin/env bash
# Smart LMS — one-line installer
# Usage: curl -fsSL https://raw.githubusercontent.com/berkanpak/SmartLMSSystem/main/install.sh | bash
set -e

REPO_URL="https://github.com/berkanpak/SmartLMSSystem.git"
# shellcheck disable=SC2034  # kept for override: SMART_LMS_DIR=... curl ... | bash
INSTALL_DIR="${SMART_LMS_DIR:-$HOME/.smart-lms-app}"

echo ""
echo "  Smart LMS MCP Installer"
echo ""

# ── clone or update ───────────────────────────────────────────────────────────
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "  Updating existing install at $INSTALL_DIR …"
  git -C "$INSTALL_DIR" pull --quiet
else
  echo "  Cloning into $INSTALL_DIR …"
  git clone --quiet "$REPO_URL" "$INSTALL_DIR"
fi

# ── run the Python installer ──────────────────────────────────────────────────
python3 "$INSTALL_DIR/install.py" --repo "$INSTALL_DIR" "$@"
