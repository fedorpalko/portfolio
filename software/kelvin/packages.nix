{ config, pkgs, lib, ... }:

let cfg = config.kelvin; in

{
  environment.systemPackages = with pkgs; lib.flatten [

    # ── Base (always installed) ────────────────────────────────────────────
    [
      # Terminal utilities
      btop eza fzf ripgrep bat fd zoxide
      fastfetch wget curl unzip zip jq
      git gh tmux

      # Media (base)
      vlc ffmpeg yt-dlp

      # System
      pciutils usbutils lshw smartmontools
      ntfs3g exfat dosfstools
      man-db man-pages

      # Kelvin tools (from ./tools/)
      # kelvin kelvin-store  # TODO: uncomment once derivations are complete
    ]

    # ── Development ─────────────────────────────────────────────────────────
    (lib.optionals cfg.useCases.development [
      vscode
      # claude-code  # TODO: package Anthropic Claude Code CLI when available in nixpkgs
      neovim
      docker-compose

      # Python
      (python3.withPackages (ps: with ps; [
        numpy pandas matplotlib scipy
        requests rich httpx
        jupyter ipython
        black ruff mypy
      ]))

      # Node
      nodejs npm

      # Other dev tools
      gnumake gcc pkg-config
      sqlite
      redis
    ])

    # ── Gaming ──────────────────────────────────────────────────────────────
    (lib.optionals cfg.useCases.gaming [
      steam
      lutris
      gamemode
      proton-ge-bin
      mangohud
      gamescope
      wine
      winetricks
    ])

    # ── Gaming Tweaks (advanced only) ──────────────────────────────────────
    (lib.optionals cfg.useCases.gamingTweaks [
      cpupower-gui   # CPU governor switching
      # schedtool    # real-time priority scheduler
    ])

    # ── Office ──────────────────────────────────────────────────────────────
    (lib.optionals cfg.useCases.office [
      libreoffice-qt6-fresh
      thunderbird
      obsidian
      kdePackages.okular  # already base but explicit here
    ])

    # ── Media ───────────────────────────────────────────────────────────────
    (lib.optionals cfg.useCases.media [
      obs-studio
      spotify
      kdenlive
      handbrake
      # vlc and ffmpeg already in base
    ])

    # ── Creative ────────────────────────────────────────────────────────────
    (lib.optionals cfg.useCases.creative [
      gimp
      inkscape
      krita
      kdenlive  # deduped by nix if also in media
    ])

    # ── Science & Data ──────────────────────────────────────────────────────
    (lib.optionals cfg.useCases.science [
      jupyter
      rPackages.tidyverse
      rstudio
      julia-bin
      texlive.combined.scheme-full
      gnuplot
      zotero
    ])

    # ── Privacy ─────────────────────────────────────────────────────────────
    (lib.optionals cfg.useCases.privacy [
      mullvad-vpn
      tor-browser
      signal-desktop
      protonmail-bridge
      keepassxc
    ])

    # ── Server & Hosting ────────────────────────────────────────────────────
    (lib.optionals cfg.useCases.server [
      portainer  # TODO: verify nixpkgs name
      nginx
      caddy
      postgresql
      redis
      mariadb
    ])

    # ── Legacy Hardware Support (advanced only) ──────────────────────────────
    (lib.optionals cfg.useCases.legacyHardware [
      linux-firmware
      # broadcom-sta  # TODO: requires kernel module via nixpkgs
    ])

    # ── Virtualization (advanced only) ──────────────────────────────────────
    (lib.optionals cfg.useCases.virtualization [
      virt-manager
      qemu
      # looking-glass-client  # TODO: requires IVSHMEM setup
    ])

    # ── Security (advanced only) ─────────────────────────────────────────────
    (lib.optionals cfg.useCases.security [
      nmap
      wireshark
      burpsuite
      metasploit
    ])

  ];

  # Steam requires 32-bit support
  hardware.steam-hardware.enable = lib.mkIf cfg.useCases.gaming true;

  # Mullvad VPN service
  services.mullvad-vpn.enable = cfg.useCases.privacy;

  # PostgreSQL service (if server use case)
  services.postgresql = lib.mkIf cfg.useCases.server {
    enable      = true;
    package     = pkgs.postgresql_16;
    enableTCPIP = false;
  };
}
