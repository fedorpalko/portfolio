#!/usr/bin/env bash
# Boot the Kelvin installer ISO in QEMU for local testing.
# Requires: qemu-system-x86_64, KVM support (/dev/kvm must exist)
#
# Usage:
#   nix build .#packages.x86_64-linux.iso   # build the ISO first
#   bash test-iso.sh                         # boot it

set -euo pipefail

# Locate the built ISO. `nix build .#iso` leaves a `result` symlink that may be
# either the ISO file itself or a directory containing it under `iso/`
# (the native nixpkgs image system puts it at `iso/kelvin-installer.iso`).
RESULT="result"

if [[ ! -e "$RESULT" ]]; then
  echo "No build output at ./$RESULT"
  echo "Build it first: nix build .#iso"
  exit 1
fi

if [[ -f "$RESULT" ]]; then
  # result is a direct symlink to the ISO file
  ISO="$RESULT"
else
  # result is a directory — find the first .iso inside it
  ISO="$(find -L "$RESULT" -type f -name '*.iso' | head -n1)"
fi

if [[ -z "${ISO:-}" || ! -f "$ISO" ]]; then
  echo "Could not find an .iso under ./$RESULT"
  echo "Build it first: nix build .#iso"
  exit 1
fi

KVM_FLAGS=()
if [[ -r /dev/kvm ]]; then
  KVM_FLAGS=(-enable-kvm -cpu host)
  echo "KVM enabled"
else
  echo "WARNING: /dev/kvm not available — running without KVM (slow)"
fi

DISK=/tmp/kelvin-test-disk.qcow2
if [[ ! -f "$DISK" ]]; then
  echo "Creating 40 GB virtual test disk at $DISK"
  qemu-img create -f qcow2 "$DISK" 40G
fi

echo "Booting $ISO ..."

exec qemu-system-x86_64 \
  -m 6144 \
  -smp 3 \
  "${KVM_FLAGS[@]}" \
  -cdrom "$ISO" \
  -boot d \
  -vga std \
  -display gtk \
  -device virtio-net-pci,netdev=net0 \
  -netdev user,id=net0 \
  -drive file=/tmp/kelvin-test-disk.qcow2,format=qcow2,if=virtio \
  -machine q35
