#!/usr/bin/env bash
# Kelvin hardware autodetection utilities
# Sourced by install.sh — do not execute directly.

# ── CPU detection ─────────────────────────────────────────────────────────────

detect_cpu() {
  local vendor
  vendor=$(lscpu 2>/dev/null | awk '/Vendor ID:/ {print $3}')
  case "$vendor" in
    AuthenticAMD) echo "amd" ;;
    GenuineIntel) echo "intel" ;;
    *)
      # Fallback: check /proc/cpuinfo
      if grep -qi "amd" /proc/cpuinfo 2>/dev/null; then
        echo "amd"
      elif grep -qi "intel" /proc/cpuinfo 2>/dev/null; then
        echo "intel"
      else
        echo "auto"
      fi
      ;;
  esac
}

# ── GPU detection ─────────────────────────────────────────────────────────────

detect_gpu() {
  # Check for discrete GPU first, then fall back to integrated
  local pci_gpu
  pci_gpu=$(lspci 2>/dev/null | grep -i "vga\|3d\|display" || true)

  if echo "$pci_gpu" | grep -qi "nvidia"; then
    echo "nvidia"
  elif echo "$pci_gpu" | grep -qi "amd\|radeon\|advanced micro"; then
    echo "amd"
  elif echo "$pci_gpu" | grep -qi "intel"; then
    echo "intel"
  else
    echo "auto"
  fi
}

# ── Disk listing ──────────────────────────────────────────────────────────────

# Returns disk list formatted for gum choose (simple mode)
detect_disks_simple() {
  local recommended
  recommended=$(detect_recommended_disk)

  while IFS= read -r disk; do
    local size model transport
    size=$(lsblk -d -n -o SIZE "/dev/${disk}" 2>/dev/null || echo "?")
    model=$(lsblk -d -n -o MODEL "/dev/${disk}" 2>/dev/null | sed 's/  */ /g;s/^ //;s/ $//' || echo "Unknown")
    transport=$(lsblk -d -n -o TRAN "/dev/${disk}" 2>/dev/null || echo "")

    local suffix=""
    [[ "/dev/${disk}" == "$recommended" ]] && suffix="   ← we recommend this one"
    [[ "$transport" == "usb" ]] && suffix="   ← USB drive"

    echo "/dev/${disk}   ${model:-Unknown}   ${size}${suffix}"
  done < <(lsblk -d -n -o NAME 2>/dev/null | grep -E '^(nvme|sd|vd|hd)')
}

# Returns disk list formatted for gum choose (advanced mode)
detect_disks_advanced() {
  while IFS= read -r disk; do
    local size model fstype transport
    size=$(lsblk -d -n -o SIZE "/dev/${disk}" 2>/dev/null || echo "?")
    model=$(lsblk -d -n -o MODEL "/dev/${disk}" 2>/dev/null | sed 's/  */ /g;s/^ //;s/ $//' || echo "Unknown")
    transport=$(lsblk -d -n -o TRAN "/dev/${disk}" 2>/dev/null || echo "")

    local tag=""
    [[ "$transport" == "usb" ]] && tag=" [USB]"

    echo "/dev/${disk}   ${model:-Unknown}   ${size}${tag}"
  done < <(lsblk -d -n -o NAME 2>/dev/null | grep -E '^(nvme|sd|vd|hd)')
}

# Recommend the most likely system disk:
# 1. Largest NVMe that isn't a USB drive
# 2. Largest SATA SSD
# 3. Largest HDD
# Explicitly avoids USB/removable media.
detect_recommended_disk() {
  local best_disk="" best_size=0

  while IFS= read -r disk; do
    local transport removable size_bytes
    transport=$(lsblk -d -n -o TRAN "/dev/${disk}" 2>/dev/null || echo "")
    removable=$(lsblk -d -n -o RM "/dev/${disk}" 2>/dev/null || echo "0")
    size_bytes=$(lsblk -d -n -o SIZE -b "/dev/${disk}" 2>/dev/null || echo "0")

    # Skip USB and removable
    [[ "$transport" == "usb" || "$removable" == "1" ]] && continue

    if (( size_bytes > best_size )); then
      best_size=$size_bytes
      best_disk="/dev/${disk}"
    fi
  done < <(lsblk -d -n -o NAME 2>/dev/null | grep -E '^(nvme|sd|vd|hd)')

  echo "$best_disk"
}

# ── UEFI detection ────────────────────────────────────────────────────────────

detect_is_uefi() {
  [[ -d /sys/firmware/efi/efivars ]] && echo "uefi" || echo "bios"
}

# ── RAM detection ─────────────────────────────────────────────────────────────

detect_ram_gb() {
  local kb
  kb=$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || echo "0")
  echo $(( kb / 1024 / 1024 ))
}
