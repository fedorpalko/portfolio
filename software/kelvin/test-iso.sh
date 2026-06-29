#!/usr/bin/env bash
# Boot the Kelvin installer ISO in QEMU for local testing.
# Requires: qemu-system-x86_64, KVM support (/dev/kvm must exist)
#
# Usage:
#   nix build .#packages.x86_64-linux.iso   # build the ISO first
#   bash test-iso.sh                         # boot it

set -euo pipefail

ISO="result/iso/kelvin-installer.iso"

if [[ ! -f "$ISO" ]]; then
  echo "ISO not found at $ISO"
  echo "Build it first: nix build .#packages.x86_64-linux.iso"
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
