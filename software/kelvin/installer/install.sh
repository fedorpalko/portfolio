#!/usr/bin/env bash
# Kelvin Installer — main entry point
# Requires: gum (charmbracelet/gum), bash 5+

set -euo pipefail

KELVIN_VERSION="0.1.0"
KELVIN_BLUE="#A8D8EA"
KELVIN_DARK="#2A2A2A"
KELVIN_WHITE="#F5F5F5"
KELVIN_ICE="#5BA4CF"
KELVIN_FROST="#E8F4FD"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Dependency check ──────────────────────────────────────────────────────────

if ! command -v gum &>/dev/null; then
  cat <<'EOF'

  ❄️  K E L V I N  ❄️

  Something's missing: gum is not installed.
  gum is what makes this installer look nice.

  Install it and try again:

    # On NixOS (in the live environment, this should already be here):
    nix-shell -p gum --run ./install.sh

    # Or on any system:
    go install github.com/charmbracelet/gum@latest

  If you booted the Kelvin ISO and see this message,
  something went wrong — please file an issue.

EOF
  exit 1
fi

if ! command -v nix &>/dev/null; then
  echo "ERROR: nix is not available. Are you booted into the Kelvin ISO?"
  exit 1
fi

# ── Source utilities ──────────────────────────────────────────────────────────

# shellcheck source=detect.sh
source "${SCRIPT_DIR}/detect.sh"

# ── Mode selection ────────────────────────────────────────────────────────────

clear

gum style \
  --foreground "$KELVIN_WHITE" \
  --background "$KELVIN_BLUE" \
  --border rounded \
  --border-foreground "$KELVIN_ICE" \
  --padding "1 4" \
  --align center \
  --width 60 \
  "❄️  K E L V I N  ❄️" \
  "" \
  "an opinionated NixOS setup" \
  "that gets out of your way once you're in." \
  "" \
  "v${KELVIN_VERSION}"

echo

MODE=$(gum choose \
  --header "How do you want to do this?" \
  --header.foreground "$KELVIN_ICE" \
  --item.foreground "$KELVIN_WHITE" \
  --selected.foreground "$KELVIN_WHITE" \
  --selected.background "$KELVIN_ICE" \
  "Simple Install   — friendly, fast, no jargon" \
  "Advanced Install — full control, no hand-holding")

echo

case "$MODE" in
  "Simple Install"*)
    export KELVIN_BG="$KELVIN_BLUE"
    export KELVIN_FG="$KELVIN_WHITE"
    # shellcheck source=simple.sh
    source "${SCRIPT_DIR}/simple.sh"
    run_simple_install
    ;;
  "Advanced Install"*)
    export KELVIN_BG="$KELVIN_DARK"
    export KELVIN_FG="$KELVIN_WHITE"
    # shellcheck source=advanced.sh
    source "${SCRIPT_DIR}/advanced.sh"
    run_advanced_install
    ;;
  *)
    echo "No mode selected. Exiting."
    exit 0
    ;;
esac
