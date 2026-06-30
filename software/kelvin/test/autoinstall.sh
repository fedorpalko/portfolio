#!/usr/bin/env bash
# Kelvin NON-INTERACTIVE test installer.
#
# This is a TEST HARNESS — it is NOT shipped to users and does NOT replace the
# real interactive installer (install.sh / simple.sh / advanced.sh). It exists
# so an autonomous build-test-fix loop can exercise the *real* install mechanics
# (disko partitioning, hardware-config generation, generate.sh's config writer +
# module copy + flake.lock, nixos-install, bootloader) without a human driving
# the gum TUI.
#
# It reuses the exact same functions the real installer uses, sourced from the
# scripts baked onto the ISO at /etc/kelvin-installer/. It feeds them a fixed
# set of answers (the same S_* variables simple.sh collects), then runs the same
# five steps simple_screen_installing() runs, in the same order.
#
# All output goes to the serial console so the host can read it from a file.
# It powers the machine off at the end so the host's QEMU process exits.

set -uo pipefail

# This script runs as a systemd oneshot service, which starts with a minimal
# PATH that lacks the installer's tools (bash, disko, nixos-install, lsblk, …).
# The real interactive installer runs from a login shell that has the full
# system profile on PATH; replicate that here so every command resolves.
export PATH="/run/current-system/sw/bin:/run/wrappers/bin:/run/current-system/sw/sbin:${PATH:-}"

INSTALLER_DIR="/etc/kelvin-installer"
TARGET_DISK="${KELVIN_TEST_DISK:-/dev/vda}"

say()  { echo "KELVIN-TEST: $*"; }
fail() { echo "KELVIN-TEST-RESULT: FAILURE ($*)"; finish 1; }

finish() {
  local code="${1:-0}"
  echo "KELVIN-TEST-DONE: exit=${code}"
  # Give the serial log a moment to flush, then power off so QEMU exits.
  sync
  sleep 2
  systemctl poweroff --no-block 2>/dev/null || poweroff -f 2>/dev/null || true
  exit "$code"
}

say "autoinstall starting on $(date -u +%FT%TZ)"
say "target disk = ${TARGET_DISK}"

# Memory headroom: the live ISO runs from a RAM-backed tmpfs, and nixos-install's
# evaluation/copy of the full desktop closure is memory-heavy. The harness
# attaches a swap block device (/dev/vdb) so the guest can spill to disk instead
# of OOM-panicking under TCG with limited RAM (tmpfs pages page out to swap too).
# Strictly a test convenience — disko only ever touches the target disk (vda).
if [[ -b /dev/vdb ]] && ! swapon --show=NAME --noheadings 2>/dev/null | grep -q '/dev/vdb'; then
  say "enabling swap on /dev/vdb"
  mkswap -f /dev/vdb >/dev/null 2>&1 || true
  swapon /dev/vdb 2>/dev/null && say "swap active: $(free -h | awk '/Swap/{print $2}')" \
    || say "warning: swapon /dev/vdb failed"
fi

# ── Fixed answers (mirror simple.sh's S_* variables) ─────────────────────────
export S_FULL_NAME="Test User"
export S_EMAIL="test@kelvin.local"
export S_USERNAME="tester"
export S_PASSWORD="testpass123"
export S_TIMEZONE="UTC"
export S_KEYBOARD="us"
export S_DISK="${TARGET_DISK}"
export S_HOSTNAME="kelvin-test"
# One use case so at least one optional module path is exercised.
export S_USECASES="Development"

# ── Sanity: scripts present? ─────────────────────────────────────────────────
[[ -d "$INSTALLER_DIR" ]] || fail "installer dir ${INSTALLER_DIR} missing"
for f in generate.sh detect.sh; do
  [[ -f "${INSTALLER_DIR}/${f}" ]] || fail "${INSTALLER_DIR}/${f} missing"
done

# ── Run a step, capturing combined output; bail on first failure ─────────────
# Each step runs in a child bash that sources generate.sh + detect.sh first, so
# both shell-function steps (partition_disk_simple, generate_kelvin_config_simple)
# and plain binaries (nixos-generate-config, nixos-install) work uniformly —
# exactly how simple.sh's _simple_step does it.
run_step() {
  local title="$1"; shift
  say ">>> STEP: ${title}"
  if bash -c '
      set -o pipefail
      source "$1"   # generate.sh
      source "$2"   # detect.sh
      shift 2
      "$@"
    ' _ "${INSTALLER_DIR}/generate.sh" "${INSTALLER_DIR}/detect.sh" "$@"; then
    say "<<< OK:   ${title}"
  else
    local rc=$?
    say "<<< FAIL (rc=${rc}): ${title}"
    fail "step failed: ${title}"
  fi
}

run_step "Partitioning ${S_DISK}" \
  partition_disk_simple "$S_DISK"

run_step "Generating hardware configuration" \
  nixos-generate-config --no-filesystems --root /mnt

run_step "Writing Kelvin configuration" \
  generate_kelvin_config_simple

run_step "Building + installing system (nixos-install)" \
  nixos-install --root /mnt \
    --flake "/mnt/home/${S_USERNAME}/.kelvin/#kelvin" \
    --no-root-passwd

run_step "Setting user password" \
  bash -c "echo '${S_USERNAME}:${S_PASSWORD}' | nixos-enter --root /mnt -- chpasswd"

say "all steps completed"
echo "KELVIN-TEST-RESULT: SUCCESS"
finish 0
