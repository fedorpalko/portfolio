{ config, pkgs, lib, ... }:

let cfg = config.kelvin; in

{
  # ── Kernel ────────────────────────────────────────────────────────────────

  boot.kernelPackages =
    if      cfg.kernel == "zen"      then pkgs.linuxPackages_zen
    else if cfg.kernel == "lts"      then pkgs.linuxPackages
    else if cfg.kernel == "latest"   then pkgs.linuxPackages_latest
    else if cfg.kernel == "hardened" then pkgs.linuxPackages_hardened
    else if cfg.kernel == "lqx"      then pkgs.linuxPackages_lqx
    else if cfg.kernel == "6_12"     then pkgs.linuxPackages_6_12
    else if cfg.kernel == "5_15"     then pkgs.linuxPackages_5_15
    else pkgs.linuxPackages_zen;

  boot.initrd.availableKernelModules = [
    "xhci_pci" "nvme" "ahci" "usb_storage" "usbhid" "sd_mod" "sr_mod"
  ];
  boot.kernelModules = [ "kvm-intel" "kvm-amd" ];

  # WORKAROUND (upstream regression): linux-zen 7.0.x in current nixpkgs installs
  # its kernel image as `vmlinuz`, but its `kernel.target` — which NixOS trusts
  # for `system.boot.loader.kernelFile` — still reports `bzImage`. The mismatch
  # makes the system build abort with:
  #   The bootloader cannot find the proper kernel image.
  #   (Expecting .../linux-zen-<ver>/bzImage)
  # Point the loader at the file the zen kernel actually produces. The 6.x
  # kernels (lts, 6_12, 5_15) ship `bzImage` as expected, so only override for
  # zen. Remove once nixpkgs' linux-zen ships `bzImage` again.
  system.boot.loader.kernelFile = lib.mkIf (cfg.kernel == "zen") "vmlinuz";

  # ── Limine (default, recommended) ────────────────────────────────────────
  # TODO: Limine NixOS module may require a community overlay or future nixpkgs support.
  # Track: https://github.com/NixOS/nixpkgs/pull/XXXXX
  # Once available, enable via:
  #
  #   boot.loader.limine.enable = true;
  #   boot.loader.limine.biosSupport = true;
  #   boot.loader.limine.maxGenerations = cfg.bootloader.generations;
  #
  # For now, Limine selection falls back to systemd-boot on UEFI or GRUB on BIOS.

  boot.loader = lib.mkMerge [

    (lib.mkIf (cfg.bootloader.type == "limine") (lib.mkMerge [
      # TODO: replace with boot.loader.limine.* once module is available in nixpkgs
      (lib.mkIf true {
        systemd-boot.enable = true;
        systemd-boot.configurationLimit = cfg.bootloader.generations;
        efi.canTouchEfiVariables = true;
      })
    ]))

    (lib.mkIf (cfg.bootloader.type == "systemd-boot") {
      systemd-boot.enable = true;
      systemd-boot.configurationLimit = cfg.bootloader.generations;
      efi.canTouchEfiVariables = true;
    })

    (lib.mkIf (cfg.bootloader.type == "grub") {
      grub = {
        enable      = true;
        device      = "nodev";
        efiSupport  = true;
        useOSProber = false;
        # TODO: apply Kelvin GRUB theme wallpaper from assets/
      };
      efi.canTouchEfiVariables = true;
    })

  ];

  # ── Boot splash ───────────────────────────────────────────────────────────
  boot.plymouth.enable = true;
  # TODO: set boot.plymouth.theme to a Kelvin-branded theme once assets are finalized

  # ── Tmp on tmpfs ─────────────────────────────────────────────────────────
  boot.tmp.useTmpfs   = true;
  boot.tmp.tmpfsSize  = "25%";
}
