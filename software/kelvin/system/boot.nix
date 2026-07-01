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

  # ── Limine (default, recommended) ────────────────────────────────────────
  # Real Limine via the nixpkgs boot.loader.limine module. UEFI only for now
  # (Kelvin targets modern UEFI machines); BIOS installs should pick GRUB.

  boot.loader = lib.mkMerge [

    (lib.mkIf (cfg.bootloader.type == "limine") {
      limine = {
        enable     = true;
        efiSupport = true;
        # Install Limine to the removable-media path (EFI/BOOT/BOOTX64.EFI)
        # rather than registering an NVRAM boot entry. This is the robust choice
        # across every target Kelvin runs on — QEMU/OVMF (whose NVRAM we reset on
        # each boot) and Macs (whose EFI variables are unreliable to write). It
        # implies we must not touch EFI variables (see efi.canTouchEfiVariables).
        efiInstallAsRemovable = true;
        maxGenerations = cfg.bootloader.generations;

        style = {
          # A solid Kelvin boot background stretched to fill the screen; it
          # supplies the backdrop colour, so the graphical terminal is left
          # transparent on top. light = Kelvin Blue, dark = Kelvin Dark.
          wallpapers = [
            (if cfg.bootloader.theme == "light"
             then ../assets/kelvin-boot-light.png
             else ../assets/kelvin-boot-dark.png)
          ];
          wallpaperStyle = "stretched";

          interface = {
            branding        = "❄  K E L V I N  ❄";
            brandingColor   = if cfg.bootloader.theme == "light" then "2A2A2A" else "A8D8EA";
            helpColor       = "5BA4CF";
            helpColorBright = "A8D8EA";
          };

          graphicalTerminal = {
            foreground       = if cfg.bootloader.theme == "light" then "2A2A2A" else "F5F5F5";
            brightForeground = "FFFFFF";
            # A little breathing room around the menu so it doesn't hug the edge.
            margin           = 32;
            marginGradient   = 4;
          };
        };
      };
      # Companion to efiInstallAsRemovable: do not manage NVRAM boot entries.
      efi.canTouchEfiVariables = false;
    })

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

    # Snappy but not blink-and-miss-it menu (applies to whichever loader is on).
    { timeout = lib.mkDefault 3; }

  ];

  # ── Boot splash ───────────────────────────────────────────────────────────
  boot.plymouth.enable = true;
  # A calm dark boot splash under the bootloader. bgrt shows the firmware logo
  # centered on black — clean and vendor-neutral, matches the dark Kelvin theme.
  boot.plymouth.theme = lib.mkDefault "bgrt";
  # Quiet the console so the splash isn't interrupted by kernel log spam.
  boot.kernelParams = [ "quiet" "splash" "rd.udev.log_level=3" "vt.global_cursor_default=0" ];
  boot.consoleLogLevel = 3;
  boot.initrd.verbose = false;

  # ── Tmp on tmpfs ─────────────────────────────────────────────────────────
  boot.tmp.useTmpfs   = true;
  boot.tmp.tmpfsSize  = "25%";
}
