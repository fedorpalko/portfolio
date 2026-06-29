{ config, pkgs, lib, ... }:

let cfg = config.kelvin; in

{
  # ── zram ──────────────────────────────────────────────────────────────────

  zramSwap = lib.mkIf (cfg.swap == "zram" || cfg.swap == "zram+swapfile") {
    enable        = true;
    algorithm     = "zstd";
    memoryPercent = 50;
  };

  # Swapfile for zram+swapfile or swapfile-only modes
  # TODO: declaratively create the swapfile and add it to swapDevices.
  # The installer handles mkswap + swapon during partitioning.
  # Post-install: add entry here once the swapfile exists.
  #
  # swapDevices = lib.optional
  #   (cfg.swap == "swapfile" || cfg.swap == "zram+swapfile")
  #   { device = "/var/lib/swapfile"; size = cfg.swapSize * 1024; };

  # ── Kernel VM tunables ────────────────────────────────────────────────────

  boot.kernel.sysctl = {
    # Low swappiness keeps things in RAM as long as possible
    "vm.swappiness"             = lib.mkIf (cfg.swap != "none") 10;
    "vm.vfs_cache_pressure"     = 50;
    "vm.dirty_ratio"            = 10;
    "vm.dirty_background_ratio" = 5;
    # Increase inotify watches for VSCode, IDEs, etc.
    "fs.inotify.max_user_watches" = 524288;
  };

  # ── ananicy-cpp — process priority daemon ─────────────────────────────────

  services.ananicy = lib.mkIf cfg.services.ananicy {
    enable  = true;
    package = pkgs.ananicy-cpp;
    # Uses the built-in rule sets from ananicy-rules-cachyos when available
  };

  # ── Scheduler tuning ──────────────────────────────────────────────────────

  # scx_lavd / scx_rusty scheduler (CachyOS-style desktop tuning)
  # TODO: enable once scx_schedulers is stable in nixpkgs-unstable
  # services.scx.enable = true;
  # services.scx.scheduler = "scx_lavd";

  # ── Nix build performance ─────────────────────────────────────────────────

  nix.settings.max-jobs = "auto";
}
