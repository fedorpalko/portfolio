#!/usr/bin/env bash
# Boot a Kelvin installer ISO in QEMU for local / automated testing.
#
# Two modes:
#   * Interactive (default ISO):  bash test-iso.sh
#       Boots .#iso in a GTK window with KVM if available — for a human to click
#       through the real gum TUI.
#   * Headless autotest:          KELVIN_HEADLESS=1 bash test-iso.sh
#       Boots .#iso-test with NO display, redirects the serial console to a log
#       file, and runs the non-interactive autoinstall. Intended for the
#       autonomous build-test-fix loop — read the result straight from the log.
#
# Build the ISO first:
#   nix build .#iso         # interactive
#   nix build .#iso-test    # headless autotest   (-> ./result)
#
# Env knobs (headless mode):
#   KELVIN_HEADLESS=1            enable headless serial autotest mode
#   KELVIN_SERIAL_LOG=PATH       serial log file        (default /tmp/kelvin-boot.log)
#   KELVIN_DISK=PATH             qcow2 test disk         (default /tmp/kelvin-test-disk.qcow2)
#   KELVIN_DISK_FRESH=1          recreate the disk before booting (default 1 in headless)
#   KELVIN_TIMEOUT=SECONDS       hard cap on the QEMU run (default 5400)
#   KELVIN_MEM_MB=MB             guest RAM               (default 4096)
#   KELVIN_SWAP_GB=GB            guest swap disk (/dev/vdb), 0 disables (default 12)
#   KELVIN_SMP=N                 guest vCPUs             (default 4)
#   KELVIN_CACHE_DIR=PATH        host binary cache dir to serve at 10.0.2.2:8000
#   KELVIN_ISO=PATH              explicit ISO path (skips result lookup)

set -euo pipefail

HEADLESS="${KELVIN_HEADLESS:-0}"
SERIAL_LOG="${KELVIN_SERIAL_LOG:-/tmp/kelvin-boot.log}"
DISK="${KELVIN_DISK:-/tmp/kelvin-test-disk.qcow2}"
TIMEOUT="${KELVIN_TIMEOUT:-5400}"
MEM_MB="${KELVIN_MEM_MB:-4096}"
SWAP_GB="${KELVIN_SWAP_GB:-12}"
SMP="${KELVIN_SMP:-4}"
SWAP_DISK="${KELVIN_SWAP_DISK:-/tmp/kelvin-swap.img}"
CACHE_DIR="${KELVIN_CACHE_DIR:-}"
CACHE_PORT=8000

# ── Locate the ISO ───────────────────────────────────────────────────────────
ISO="${KELVIN_ISO:-}"
if [[ -z "$ISO" ]]; then
  RESULT="result"
  if [[ ! -e "$RESULT" ]]; then
    echo "No build output at ./$RESULT — build first: nix build .#iso-test" >&2
    exit 1
  fi
  if [[ -f "$RESULT" ]]; then
    ISO="$RESULT"
  else
    ISO="$(find -L "$RESULT" -type f -name '*.iso' | head -n1)"
  fi
fi
if [[ -z "${ISO:-}" || ! -f "$ISO" ]]; then
  echo "Could not find an .iso (looked at: ${ISO:-<none>})" >&2
  exit 1
fi

# ── KVM vs TCG ─────────────────────────────────────────────────────────────--
ACCEL_FLAGS=()
if [[ -r /dev/kvm && -w /dev/kvm ]]; then
  ACCEL_FLAGS=(-enable-kvm -cpu host)
  echo "Acceleration: KVM"
else
  # TCG software emulation. A larger TB cache speeds up long emulated runs.
  ACCEL_FLAGS=(-accel "tcg,tb-size=512" -cpu max)
  echo "Acceleration: TCG (software — no /dev/kvm). This is slow."
fi

# ── Test disk ──────────────────────────────────────────────────────────────--
FRESH="${KELVIN_DISK_FRESH:-$([[ "$HEADLESS" == 1 ]] && echo 1 || echo 0)}"
if [[ "$FRESH" == 1 || ! -f "$DISK" ]]; then
  rm -f "$DISK"
  echo "Creating fresh 40G test disk at $DISK"
  qemu-img create -f qcow2 "$DISK" 40G >/dev/null
fi

# Guest swap disk (/dev/vdb). The live ISO runs from a RAM-backed tmpfs and
# nixos-install's eval/copy of the full desktop closure is memory-heavy; on a
# RAM-constrained host we keep guest RAM modest and let the guest spill to this
# disk-backed swap instead of OOM-panicking. It's a sparse raw file, so it costs
# host disk only for pages actually used — and zero host RAM.
SWAP_ARGS=()
if [[ "$SWAP_GB" != 0 ]]; then
  rm -f "$SWAP_DISK"
  truncate -s "${SWAP_GB}G" "$SWAP_DISK"
  echo "Created sparse ${SWAP_GB}G guest swap disk at $SWAP_DISK (-> /dev/vdb)"
  SWAP_ARGS=(-drive "file=${SWAP_DISK},format=raw,if=virtio")
fi

# ── Optional host binary cache server ─────────────────────────────────────────
CACHE_PID=""
cleanup() {
  [[ -n "$CACHE_PID" ]] && kill "$CACHE_PID" 2>/dev/null || true
}
trap cleanup EXIT
if [[ -n "$CACHE_DIR" && -d "$CACHE_DIR" ]]; then
  echo "Serving host binary cache $CACHE_DIR at http://10.0.2.2:${CACHE_PORT}"
  ( cd "$CACHE_DIR" && exec python3 -m http.server "$CACHE_PORT" --bind 0.0.0.0 ) \
    >/tmp/kelvin-cache-server.log 2>&1 &
  CACHE_PID=$!
fi

# ── Common QEMU args ─────────────────────────────────────────────────────────
QEMU=(qemu-system-x86_64
  -m "$MEM_MB"
  -smp "$SMP"
  "${ACCEL_FLAGS[@]}"
  -machine q35
  -cdrom "$ISO"
  -boot d
  -device virtio-net-pci,netdev=net0
  -netdev user,id=net0
  -drive "file=${DISK},format=qcow2,if=virtio"
  "${SWAP_ARGS[@]}"
  -no-reboot
)

echo "ISO: $ISO"

if [[ "$HEADLESS" == 1 ]]; then
  : > "$SERIAL_LOG"
  echo "Headless mode — serial console -> $SERIAL_LOG (timeout ${TIMEOUT}s)"
  set +e
  timeout --signal=KILL "$TIMEOUT" \
    "${QEMU[@]}" \
      -display none \
      -serial "file:${SERIAL_LOG}" \
      -monitor none
  rc=$?
  set -e
  if [[ $rc -eq 137 ]]; then
    echo "QEMU killed by timeout (${TIMEOUT}s)."
  fi
  echo "QEMU exited (rc=$rc). Serial log: $SERIAL_LOG"
  exit $rc
else
  echo "Interactive mode — GTK window."
  exec "${QEMU[@]}" -vga std -display gtk
fi
