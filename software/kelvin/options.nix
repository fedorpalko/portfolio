{ lib, ... }:

let inherit (lib) mkOption types; in

{
  options.kelvin = {

    # ── Identity ──────────────────────────────────────────────────────────────

    hostname = mkOption {
      type        = types.str;
      default     = "kelvin";
      description = "System hostname.";
    };

    username = mkOption {
      type        = types.str;
      default     = "user";
      description = "Primary user account name.";
    };

    fullName = mkOption {
      type        = types.str;
      default     = "Kelvin User";
      description = "Full name for git config and display.";
    };

    email = mkOption {
      type        = types.str;
      default     = "user@example.com";
      description = "Email address for git config.";
    };

    timezone = mkOption {
      type        = types.str;
      default     = "UTC";
      example     = "Europe/Bratislava";
      description = "System timezone (TZ database name).";
    };

    locale = mkOption {
      type        = types.str;
      default     = "en_US.UTF-8";
      description = "System locale (LC_ALL / LANG).";
    };

    keyboardLayout = mkOption {
      type        = types.str;
      default     = "us";
      description = "X11 and console keyboard layout.";
    };

    disk = mkOption {
      type        = types.str;
      default     = "/dev/sda";
      example     = "/dev/nvme0n1";
      description = "Block device Kelvin is installed on. Set by the installer; used by disko.";
    };

    # ── Hardware ──────────────────────────────────────────────────────────────

    gpu = mkOption {
      type        = types.enum [ "amd" "nvidia" "intel" "auto" ];
      default     = "auto";
      description = "GPU type for driver configuration.";
    };

    cpu = mkOption {
      type        = types.enum [ "amd" "intel" "auto" ];
      default     = "auto";
      description = "CPU manufacturer for microcode selection.";
    };

    arch = mkOption {
      type        = types.enum [ "x86_64" "aarch64" ];
      default     = "x86_64";
      description = "System architecture.";
    };

    # ── Bootloader ────────────────────────────────────────────────────────────

    bootloader = {
      type = mkOption {
        type        = types.enum [ "limine" "systemd-boot" "grub" ];
        default     = "limine";
        description = "Bootloader to install. Limine recommended.";
      };

      theme = mkOption {
        type        = types.enum [ "light" "dark" ];
        default     = "dark";
        description = "Boot splash theme. light = Kelvin Blue (#A8D8EA), dark = Kelvin Dark (#2A2A2A).";
      };

      generations = mkOption {
        type        = types.int;
        default     = 2;
        description = "Number of NixOS generations to keep in the bootloader menu.";
      };
    };

    # ── Filesystem ────────────────────────────────────────────────────────────

    filesystem = mkOption {
      type        = types.enum [ "btrfs" "ext4" "xfs" ];
      default     = "btrfs";
      description = "Root filesystem type. BTRFS recommended.";
    };

    zstdCompression = mkOption {
      type        = types.bool;
      default     = true;
      description = "Enable zstd transparent compression (BTRFS only).";
    };

    swap = mkOption {
      type        = types.enum [ "zram" "zram+swapfile" "swapfile" "none" ];
      default     = "zram";
      description = "Swap configuration. zram recommended.";
    };

    swapSize = mkOption {
      type        = types.int;
      default     = 0;
      description = "Swapfile size in GB. Only used when swap includes a swapfile.";
    };

    # ── Channel ───────────────────────────────────────────────────────────────

    channel = mkOption {
      type        = types.enum [ "unstable" "stable" ];
      default     = "unstable";
      description = "NixOS channel to track. Kelvin is built and tested on unstable.";
    };

    # ── Kernel ────────────────────────────────────────────────────────────────

    kernel = mkOption {
      type        = types.enum [ "zen" "lts" "latest" "hardened" "lqx" "6_12" "5_15" ];
      default     = "zen";
      description = "Kernel package selection. Zen recommended for desktop use.";
    };

    # ── Use Cases ─────────────────────────────────────────────────────────────

    useCases = {
      development = mkOption {
        type        = types.bool;
        default     = false;
        description = "VSCode, Claude Code, Docker, Python, Node, Neovim, etc.";
      };
      gaming = mkOption {
        type        = types.bool;
        default     = false;
        description = "Steam, Lutris, Proton-GE, MangoHud, Gamescope, Wine.";
      };
      gamingTweaks = mkOption {
        type        = types.bool;
        default     = false;
        description = "CPU governor switching, low-latency audio, gamemode tweaks. Advanced only.";
      };
      office = mkOption {
        type        = types.bool;
        default     = false;
        description = "LibreOffice, Thunderbird, Obsidian, Okular.";
      };
      media = mkOption {
        type        = types.bool;
        default     = false;
        description = "OBS, Spotify, Kdenlive, Handbrake.";
      };
      creative = mkOption {
        type        = types.bool;
        default     = false;
        description = "GIMP, Inkscape, Krita, Kdenlive.";
      };
      science = mkOption {
        type        = types.bool;
        default     = false;
        description = "Jupyter, R, RStudio, Julia, TeXLive, gnuplot, SageMath, Zotero.";
      };
      privacy = mkOption {
        type        = types.bool;
        default     = false;
        description = "Mullvad VPN, Tor Browser, Signal, ProtonMail Bridge, KeePassXC.";
      };
      server = mkOption {
        type        = types.bool;
        default     = false;
        description = "Portainer, nginx, Caddy, PostgreSQL, Redis, MariaDB.";
      };
      legacyHardware = mkOption {
        type        = types.bool;
        default     = false;
        description = "Extended firmware blobs, Broadcom WiFi, DKMS modules. Advanced only.";
      };
      virtualization = mkOption {
        type        = types.bool;
        default     = false;
        description = "virt-manager, QEMU, KVM, libvirt, Looking Glass. Advanced only.";
      };
      security = mkOption {
        type        = types.bool;
        default     = false;
        description = "nmap, Wireshark, BurpSuite, Metasploit. Advanced only — you know what you're doing.";
      };
    };

    # ── Desktop ───────────────────────────────────────────────────────────────

    desktop = {
      iconPack = mkOption {
        type        = types.enum [ "papirus-dark" "papirus-light" "breeze" "oxygen" "tela" ];
        default     = "papirus-dark";
        description = "KDE icon pack.";
      };

      font = mkOption {
        type        = types.enum [ "inter" "ibm-plex" "noto" "google-sans" "caskaydia" ];
        default     = "inter";
        description = "System UI font. inter recommended; google-sans is a legacy alias for inter.";
      };

      colorScheme = mkOption {
        type        = types.enum [ "orchis-dark" "breeze-dark" "breeze-light" "nordic" ];
        default     = "orchis-dark";
        description = "KDE Plasma color scheme.";
      };
    };

    # ── Services ──────────────────────────────────────────────────────────────

    services = {
      ssh = mkOption {
        type        = types.bool;
        default     = true;
        description = "Enable OpenSSH daemon.";
      };
      cups = mkOption {
        type        = types.bool;
        default     = true;
        description = "Enable CUPS printing service.";
      };
      bluetooth = mkOption {
        type        = types.bool;
        default     = true;
        description = "Enable Bluetooth support.";
      };
      docker = mkOption {
        type        = types.bool;
        default     = false;
        description = "Enable Docker daemon. Auto-enabled when useCases.development is true.";
      };
      tailscale = mkOption {
        type        = types.bool;
        default     = false;
        description = "Enable Tailscale VPN mesh.";
      };
      syncthing = mkOption {
        type        = types.bool;
        default     = false;
        description = "Enable Syncthing file synchronisation.";
      };
      fail2ban = mkOption {
        type        = types.bool;
        default     = false;
        description = "Enable fail2ban brute-force protection. Recommended when SSH is enabled.";
      };
      ananicy = mkOption {
        type        = types.bool;
        default     = true;
        description = "Enable ananicy-cpp process priority daemon. Great for desktop responsiveness.";
      };
    };

  };
}
