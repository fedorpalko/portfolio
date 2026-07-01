#!/usr/bin/env bash
# Kelvin NON-INTERACTIVE test installer — ADVANCED MODE path.
#
# Sibling of test/autoinstall.sh, but exercises the *advanced* installer code
# path instead of the simple one. It is a TEST HARNESS — NOT shipped to users,
# NOT a replacement for the real interactive installer (advanced.sh drives the
# gum TUI). It feeds generate.sh the exact A_* variables advanced.sh collects
# (already mapped to their enum values, e.g. font=inter, icons=papirus-dark),
# then runs the same steps advanced_screen_installing() runs, in order:
#   partition_disk_advanced → nixos-generate-config → generate_kelvin_config_advanced
#   → nixos-install → chpasswd.
#
# All output goes to the serial console so the host can read it from a file.
# It powers the machine off at the end so the host's QEMU process exits.

set -uo pipefail

# systemd oneshot services start with a minimal PATH lacking the installer's
# tools; the real installer runs from a login shell with the full profile.
# Replicate that so every command resolves.
export PATH="/run/current-system/sw/bin:/run/wrappers/bin:/run/current-system/sw/sbin:${PATH:-}"

INSTALLER_DIR="/etc/kelvin-installer"
TARGET_DISK="${KELVIN_TEST_DISK:-/dev/vda}"

say()  { echo "KELVIN-TEST: $*"; }
fail() { echo "KELVIN-TEST-RESULT: FAILURE ($*)"; finish 1; }

finish() {
  local code="${1:-0}"
  echo "KELVIN-TEST-DONE: exit=${code}"
  sync
  sleep 2
  systemctl poweroff --no-block 2>/dev/null || poweroff -f 2>/dev/null || true
  exit "$code"
}

say "ADVANCED autoinstall starting on $(date -u +%FT%TZ)"
say "target disk = ${TARGET_DISK}"

# Swap headroom for TCG/low-RAM guests (see autoinstall.sh for rationale).
if [[ -b /dev/vdb ]] && ! swapon --show=NAME --noheadings 2>/dev/null | grep -q '/dev/vdb'; then
  say "enabling swap on /dev/vdb"
  mkswap -f /dev/vdb >/dev/null 2>&1 || true
  swapon /dev/vdb 2>/dev/null && say "swap active: $(free -h | awk '/Swap/{print $2}')" \
    || say "warning: swapon /dev/vdb failed"
fi

# ── Fixed answers (mirror advanced.sh's A_* variables, post-mapping) ─────────
# These are the values advanced.sh holds AFTER its gum screens map the human
# labels to enum values — so font is "inter", icons "papirus-dark", etc.
export A_FULL_NAME="Advanced Tester"
export A_EMAIL="adv@kelvin.local"
export A_USERNAME="tester"
export A_PASSWORD="testpass123"
export A_HOSTNAME="kelvin-adv"
export A_DISK="${TARGET_DISK}"
export A_TIMEZONE="UTC"
export A_KEYBOARD="us"                 # US QWERTY
export A_ARCH="x86_64"
export A_CPU="auto"
export A_GPU="auto"
export A_BOOTLOADER="limine"           # real Limine now (boot.loader.limine.*)
export A_BOOT_THEME="dark"             # dark Kelvin boot theme
export A_FILESYSTEM="btrfs"
export A_COMPRESSION="yes"
export A_SWAP="zram"
export A_SWAP_SIZE="0"
export A_CHANNEL="unstable"
export A_KERNEL="zen"
export A_ANANICY="yes"
export A_ICON_PACK="papirus-dark"
export A_FONT="inter"                  # the star of this run — verify Inter is the real UI font
export A_COLOR_SCHEME="orchis-dark"
# Newline-separated use-case labels, as gum choose --no-limit would emit.
export A_USECASES="Development"
# Space/label string, matched by grep -qi in generate_kelvin_config_advanced.
export A_SERVICES="SSH CUPS Bluetooth"

# ── Sanity: scripts present? ─────────────────────────────────────────────────
[[ -d "$INSTALLER_DIR" ]] || fail "installer dir ${INSTALLER_DIR} missing"
for f in generate.sh detect.sh; do
  [[ -f "${INSTALLER_DIR}/${f}" ]] || fail "${INSTALLER_DIR}/${f} missing"
done

# ── Run a step, capturing combined output; bail on first failure ─────────────
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

# Mirror advanced_screen_installing() exactly.
run_step "Partitioning ${A_DISK}" \
  partition_disk_advanced "$A_DISK" "$A_FILESYSTEM" "$A_SWAP" "$A_SWAP_SIZE" "$A_COMPRESSION"

run_step "Generating hardware configuration" \
  nixos-generate-config --no-filesystems --root /mnt

run_step "Writing Kelvin configuration (advanced)" \
  generate_kelvin_config_advanced

run_step "Building + installing system (nixos-install)" \
  nixos-install --root /mnt \
    --flake "/mnt/home/${A_USERNAME}/.kelvin/#kelvin" \
    --no-root-passwd

run_step "Setting user password" \
  bash -c "echo '${A_USERNAME}:${A_PASSWORD}' | nixos-enter --root /mnt -- chpasswd"

say "all steps completed"
echo "KELVIN-TEST-RESULT: SUCCESS"
finish 0
