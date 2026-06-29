#!/usr/bin/env bash
# Kelvin config generation
# Takes the collected installer answers and writes the ~/.kelvin/ directory.
# Sourced by simple.sh and advanced.sh — do not execute directly.

# ── Partition helpers ─────────────────────────────────────────────────────────

partition_disk_simple() {
  local disk="$1"

  # Wipe and create GPT
  parted -s "$disk" mklabel gpt

  # EFI partition: 512MB
  parted -s "$disk" mkpart ESP fat32 1MiB 513MiB
  parted -s "$disk" set 1 esp on

  # Root: rest of disk
  parted -s "$disk" mkpart primary btrfs 513MiB 100%

  # Determine partition device names (nvme vs sata naming)
  local efi_part root_part
  if [[ "$disk" == *"nvme"* ]]; then
    efi_part="${disk}p1"
    root_part="${disk}p2"
  else
    efi_part="${disk}1"
    root_part="${disk}2"
  fi

  # Format
  mkfs.fat -F 32 -n EFI "$efi_part"
  mkfs.btrfs -L nixos "$root_part" -f

  # Mount with BTRFS subvolumes
  mount "$root_part" /mnt
  btrfs subvolume create /mnt/@
  btrfs subvolume create /mnt/@home
  btrfs subvolume create /mnt/@nix
  btrfs subvolume create /mnt/@snapshots
  umount /mnt

  mount -o subvol=@,compress=zstd,noatime "$root_part" /mnt
  mkdir -p /mnt/{boot,home,nix,.snapshots}
  mount -o subvol=@home,compress=zstd,noatime "$root_part" /mnt/home
  mount -o subvol=@nix,compress=zstd,noatime  "$root_part" /mnt/nix
  mount -o subvol=@snapshots                   "$root_part" /mnt/.snapshots
  mount "$efi_part" /mnt/boot
}

partition_disk_advanced() {
  local disk="$1"
  local filesystem="${2:-btrfs}"
  local swap="${3:-zram}"
  local swap_size="${4:-0}"
  local compression="${5:-yes}"

  parted -s "$disk" mklabel gpt
  parted -s "$disk" mkpart ESP fat32 1MiB 513MiB
  parted -s "$disk" set 1 esp on

  local start="513MiB"

  # Create swapfile partition if requested
  if [[ "$swap" == "swapfile" || "$swap" == "zram+swapfile" ]]; then
    local swap_end
    swap_end="${start} + ${swap_size}GiB"
    # Leave as file in root; don't partition for it
    : # swapfile will be created post-mount
  fi

  parted -s "$disk" mkpart primary "$filesystem" "$start" 100%

  local efi_part root_part
  if [[ "$disk" == *"nvme"* ]]; then
    efi_part="${disk}p1"
    root_part="${disk}p2"
  else
    efi_part="${disk}1"
    root_part="${disk}2"
  fi

  mkfs.fat -F 32 -n EFI "$efi_part"

  case "$filesystem" in
    btrfs)
      mkfs.btrfs -L nixos "$root_part" -f
      mount "$root_part" /mnt
      btrfs subvolume create /mnt/@
      btrfs subvolume create /mnt/@home
      btrfs subvolume create /mnt/@nix
      btrfs subvolume create /mnt/@snapshots
      umount /mnt

      local compress_opts=""
      [[ "$compression" == "yes" ]] && compress_opts=",compress=zstd"

      mount -o "subvol=@,noatime${compress_opts}" "$root_part" /mnt
      mkdir -p /mnt/{boot,home,nix,.snapshots}
      mount -o "subvol=@home,noatime${compress_opts}" "$root_part" /mnt/home
      mount -o "subvol=@nix,noatime${compress_opts}"  "$root_part" /mnt/nix
      mount -o "subvol=@snapshots"                     "$root_part" /mnt/.snapshots
      ;;
    ext4)
      mkfs.ext4 -L nixos "$root_part"
      mount "$root_part" /mnt
      mkdir -p /mnt/{boot,home}
      ;;
    xfs)
      mkfs.xfs -L nixos "$root_part"
      mount "$root_part" /mnt
      mkdir -p /mnt/{boot,home}
      ;;
  esac

  mount "$efi_part" /mnt/boot
}

# ── Config generation — Simple mode ──────────────────────────────────────────

generate_kelvin_config_simple() {
  local kelvin_dir="/mnt/home/${S_USERNAME}/.kelvin"
  mkdir -p "$kelvin_dir"

  # Map selected use cases to option flags
  local dev="false" gaming="false" office="false" media="false" creative="false"
  local science="false" privacy="false" server="false"

  echo "$S_USECASES" | while IFS= read -r line; do
    case "$line" in
      "Development"*) echo "development" ;;
      "Gaming"*)      echo "gaming" ;;
      "Office"*)      echo "office" ;;
      "Media"*)       echo "media" ;;
      "Creative"*)    echo "creative" ;;
      "Science"*)     echo "science" ;;
      "Privacy"*)     echo "privacy" ;;
      "Server"*)      echo "server" ;;
    esac
  done > /tmp/kelvin_usecases

  [[ $(grep -c "development" /tmp/kelvin_usecases) -gt 0 ]] && dev="true"
  [[ $(grep -c "gaming"      /tmp/kelvin_usecases) -gt 0 ]] && gaming="true"
  [[ $(grep -c "office"      /tmp/kelvin_usecases) -gt 0 ]] && office="true"
  [[ $(grep -c "media"       /tmp/kelvin_usecases) -gt 0 ]] && media="true"
  [[ $(grep -c "creative"    /tmp/kelvin_usecases) -gt 0 ]] && creative="true"
  [[ $(grep -c "science"     /tmp/kelvin_usecases) -gt 0 ]] && science="true"
  [[ $(grep -c "privacy"     /tmp/kelvin_usecases) -gt 0 ]] && privacy="true"
  [[ $(grep -c "server"      /tmp/kelvin_usecases) -gt 0 ]] && server="true"

  _write_options_nix "$kelvin_dir" \
    "${S_HOSTNAME:-kelvin-pc}" \
    "$S_USERNAME" \
    "$S_FULL_NAME" \
    "$S_EMAIL" \
    "$S_TIMEZONE" \
    "en_US.UTF-8" \
    "$S_KEYBOARD" \
    "auto" "auto" "x86_64" \
    "limine" "dark" "2" \
    "btrfs" "true" "zram" "0" \
    "unstable" "zen" \
    "$dev" "$gaming" "false" "$office" "$media" "$creative" "$science" "$privacy" "$server" "false" "false" "false" \
    "papirus-dark" "google-sans" "orchis-dark" \
    "true" "true" "true" "$dev" "false" "false" "false" "true"

  _write_flake_nix "$kelvin_dir"
  _copy_kelvin_modules "$kelvin_dir"
  _write_hardware_config "$kelvin_dir"

  # Permissions
  chown -R "${S_USERNAME}:users" "$kelvin_dir" 2>/dev/null || true
}

# ── Config generation — Advanced mode ────────────────────────────────────────

generate_kelvin_config_advanced() {
  local kelvin_dir="/mnt/home/${A_USERNAME}/.kelvin"
  mkdir -p "$kelvin_dir"

  # Parse use cases
  local dev="false" gaming="false" gaming_tweaks="false" office="false"
  local media="false" creative="false" science="false" privacy="false"
  local server="false" legacy="false" virt="false" security_tools="false"

  echo "$A_USECASES" | while IFS= read -r line; do
    case "$line" in
      "Development"*)    echo "development" ;;
      "Gaming Tweaks"*)  echo "gamingTweaks" ;;
      "Gaming"*)         echo "gaming" ;;
      "Office"*)         echo "office" ;;
      "Media"*)          echo "media" ;;
      "Creative"*)       echo "creative" ;;
      "Science"*)        echo "science" ;;
      "Privacy"*)        echo "privacy" ;;
      "Server"*)         echo "server" ;;
      "Legacy"*)         echo "legacyHardware" ;;
      "Virtualization"*) echo "virtualization" ;;
      "Security"*)       echo "security" ;;
    esac
  done > /tmp/kelvin_usecases_adv

  [[ $(grep -c "development"   /tmp/kelvin_usecases_adv) -gt 0 ]] && dev="true"
  [[ $(grep -c "gaming$"       /tmp/kelvin_usecases_adv) -gt 0 ]] && gaming="true"
  [[ $(grep -c "gamingTweaks"  /tmp/kelvin_usecases_adv) -gt 0 ]] && gaming_tweaks="true"
  [[ $(grep -c "office"        /tmp/kelvin_usecases_adv) -gt 0 ]] && office="true"
  [[ $(grep -c "media"         /tmp/kelvin_usecases_adv) -gt 0 ]] && media="true"
  [[ $(grep -c "creative"      /tmp/kelvin_usecases_adv) -gt 0 ]] && creative="true"
  [[ $(grep -c "science"       /tmp/kelvin_usecases_adv) -gt 0 ]] && science="true"
  [[ $(grep -c "privacy"       /tmp/kelvin_usecases_adv) -gt 0 ]] && privacy="true"
  [[ $(grep -c "server"        /tmp/kelvin_usecases_adv) -gt 0 ]] && server="true"
  [[ $(grep -c "legacyHardware" /tmp/kelvin_usecases_adv) -gt 0 ]] && legacy="true"
  [[ $(grep -c "virtualization" /tmp/kelvin_usecases_adv) -gt 0 ]] && virt="true"
  [[ $(grep -c "security"      /tmp/kelvin_usecases_adv) -gt 0 ]] && security_tools="true"

  # Parse services
  local ssh="false" cups="false" bluetooth="false" docker="false"
  local tailscale="false" syncthing="false" fail2ban="false"
  local ananicy="${A_ANANICY:-yes}"
  [[ "$ananicy" == "yes" ]] && ananicy="true" || ananicy="false"

  echo "$A_SERVICES" | grep -qi "SSH"           && ssh="true"
  echo "$A_SERVICES" | grep -qi "CUPS"          && cups="true"
  echo "$A_SERVICES" | grep -qi "Bluetooth"     && bluetooth="true"
  echo "$A_SERVICES" | grep -qi "Docker"        && docker="true"
  echo "$A_SERVICES" | grep -qi "Tailscale"     && tailscale="true"
  echo "$A_SERVICES" | grep -qi "Syncthing"     && syncthing="true"
  echo "$A_SERVICES" | grep -qi "fail2ban"      && fail2ban="true"
  [[ "$dev" == "true" ]] && docker="true"

  local compression="true"
  [[ "$A_COMPRESSION" == "no" ]] && compression="false"

  _write_options_nix "$kelvin_dir" \
    "$A_HOSTNAME" "$A_USERNAME" "$A_FULL_NAME" "$A_EMAIL" \
    "$A_TIMEZONE" "en_US.UTF-8" "$A_KEYBOARD" \
    "$A_GPU" "$A_CPU" "$A_ARCH" \
    "$A_BOOTLOADER" "$A_BOOT_THEME" "2" \
    "$A_FILESYSTEM" "$compression" "$A_SWAP" "${A_SWAP_SIZE:-0}" \
    "$A_CHANNEL" "$A_KERNEL" \
    "$dev" "$gaming" "$gaming_tweaks" "$office" "$media" "$creative" "$science" "$privacy" "$server" "$legacy" "$virt" "$security_tools" \
    "$A_ICON_PACK" "$A_FONT" "$A_COLOR_SCHEME" \
    "$ssh" "$cups" "$bluetooth" "$docker" "$tailscale" "$syncthing" "$fail2ban" "$ananicy"

  _write_flake_nix "$kelvin_dir"
  _copy_kelvin_modules "$kelvin_dir"
  _write_hardware_config "$kelvin_dir"

  chown -R "${A_USERNAME}:users" "$kelvin_dir" 2>/dev/null || true
}

# ── options.nix writer ────────────────────────────────────────────────────────

_write_options_nix() {
  local dir="$1"
  local hostname="$2"   username="$3"   fullname="$4"    email="$5"
  local timezone="$6"   locale="$7"     keyboard="$8"
  local gpu="$9"        cpu="${10}"     arch="${11}"
  local bootloader="${12}" boot_theme="${13}" generations="${14}"
  local filesystem="${15}" zstd="${16}"  swap="${17}"      swap_size="${18}"
  local channel="${19}"    kernel="${20}"
  local uc_dev="${21}"     uc_gaming="${22}"  uc_gaming_tweaks="${23}"
  local uc_office="${24}"  uc_media="${25}"   uc_creative="${26}"
  local uc_science="${27}" uc_privacy="${28}" uc_server="${29}"
  local uc_legacy="${30}"  uc_virt="${31}"    uc_security="${32}"
  local icon_pack="${33}"  font="${34}"       color_scheme="${35}"
  local svc_ssh="${36}"    svc_cups="${37}"   svc_bt="${38}"
  local svc_docker="${39}" svc_ts="${40}"     svc_sync="${41}"
  local svc_f2b="${42}"    svc_ananicy="${43}"

  cat > "${dir}/options.nix" <<OPTEOF
# ~/.kelvin/options.nix
# Generated by the Kelvin installer. Edit freely.
# Apply changes: kelvin update  (or sudo nixos-rebuild switch --flake ~/.kelvin/#kelvin)
{
  kelvin = {
    # Identity
    hostname       = "${hostname}";
    username       = "${username}";
    fullName       = "${fullname}";
    email          = "${email}";
    timezone       = "${timezone}";
    locale         = "${locale}";
    keyboardLayout = "${keyboard}";

    # Hardware
    gpu  = "${gpu}";
    cpu  = "${cpu}";
    arch = "${arch}";

    # Bootloader
    bootloader = {
      type        = "${bootloader}";
      theme       = "${boot_theme}";
      generations = ${generations};
    };

    # Filesystem
    filesystem      = "${filesystem}";
    zstdCompression = ${zstd};
    swap            = "${swap}";
    swapSize        = ${swap_size};

    # Channel + Kernel
    channel = "${channel}";
    kernel  = "${kernel}";

    # Use cases
    useCases = {
      development    = ${uc_dev};
      gaming         = ${uc_gaming};
      gamingTweaks   = ${uc_gaming_tweaks};
      office         = ${uc_office};
      media          = ${uc_media};
      creative       = ${uc_creative};
      science        = ${uc_science};
      privacy        = ${uc_privacy};
      server         = ${uc_server};
      legacyHardware = ${uc_legacy};
      virtualization = ${uc_virt};
      security       = ${uc_security};
    };

    # Desktop
    desktop = {
      iconPack    = "${icon_pack}";
      font        = "${font}";
      colorScheme = "${color_scheme}";
    };

    # Services
    services = {
      ssh        = ${svc_ssh};
      cups       = ${svc_cups};
      bluetooth  = ${svc_bt};
      docker     = ${svc_docker};
      tailscale  = ${svc_ts};
      syncthing  = ${svc_sync};
      fail2ban   = ${svc_f2b};
      ananicy    = ${svc_ananicy};
    };
  };
}
OPTEOF
}

# ── flake.nix writer ──────────────────────────────────────────────────────────

_write_flake_nix() {
  local dir="$1"

  cat > "${dir}/flake.nix" <<'FLKEOF'
{
  description = "Kelvin — my personal NixOS configuration";

  inputs = {
    nixpkgs.url     = "github:NixOS/nixpkgs/nixos-unstable";
    home-manager    = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, home-manager, ... }: {
    nixosConfigurations.kelvin = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        ./options.nix
        ./configuration.nix
        home-manager.nixosModules.home-manager
      ];
    };
  };
}
FLKEOF
}

# ── Copy module tree ──────────────────────────────────────────────────────────

_copy_kelvin_modules() {
  local dir="$1"
  local kelvin_source

  # Find where the Kelvin repo lives on the ISO
  if [[ -d /etc/kelvin ]]; then
    kelvin_source="/etc/kelvin"
  elif [[ -d /etc/kelvin-installer ]]; then
    kelvin_source="/etc/kelvin-installer"
  else
    echo "WARNING: Could not find Kelvin source modules. Skipping copy." >&2
    return 0
  fi

  for subdir in system hardware desktop home assets; do
    [[ -d "${kelvin_source}/${subdir}" ]] && \
      cp -r "${kelvin_source}/${subdir}" "${dir}/"
  done

  for f in configuration.nix packages.nix; do
    [[ -f "${kelvin_source}/${f}" ]] && \
      cp "${kelvin_source}/${f}" "${dir}/"
  done
}

# ── Hardware config ───────────────────────────────────────────────────────────

_write_hardware_config() {
  local dir="$1"
  local generated="/mnt/etc/nixos/hardware-configuration.nix"

  if [[ -f "$generated" ]]; then
    mkdir -p "${dir}/hardware"
    cp "$generated" "${dir}/hardware/generated.nix"
  else
    echo "WARNING: hardware-configuration.nix not found at ${generated}" >&2
    echo "Run nixos-generate-config --root /mnt and copy the result to ${dir}/hardware/generated.nix" >&2
  fi
}
