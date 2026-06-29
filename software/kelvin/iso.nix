{ config, pkgs, lib, modulesPath, ... }:

{
  imports = [
    "${modulesPath}/installer/cd-dvd/installation-cd-minimal.nix"
  ];

  isoImage.isoName = lib.mkForce "kelvin-installer.iso";
  isoImage.makeEfiBootable  = true;
  isoImage.makeUsbBootable  = true;
  isoImage.squashfsCompression = "zstd -Xcompression-level 6";

  # Packages available in the live ISO environment
  environment.systemPackages = with pkgs; [
    gum                   # charmbracelet/gum — drives the installer TUI
    git
    curl
    wget
    parted
    util-linux
    btrfs-progs
    e2fsprogs
    xfsprogs
    dosfstools
    nixos-install-tools
    pciutils              # lspci for GPU detection
    usbutils              # lsusb
    smartmontools         # smartctl for disk info
    lshw
  ];

  # Auto-login as root on tty1 and launch the installer
  services.getty.autologinUser = lib.mkForce "root";

  systemd.services.kelvin-installer = {
    description = "Kelvin Installer";
    after       = [ "network.target" "getty@tty1.service" ];
    wantedBy    = [ "multi-user.target" ];
    serviceConfig = {
      Type      = "idle";
      TTYPath   = "/dev/tty1";
      StandardInput  = "tty";
      StandardOutput = "tty";
      ExecStart = "/etc/kelvin-installer/install.sh";
    };
  };

  # Bundle the installer scripts into the ISO
  environment.etc."kelvin-installer" = {
    source = ./installer;
    mode   = "0755";
  };

  # Networking in the live environment
  networking.networkmanager.enable = true;
  networking.wireless.enable       = false;

  # Allow root SSH during installation (optional, for debugging)
  services.openssh = {
    enable      = true;
    settings.PermitRootLogin = "yes";
  };

  system.stateVersion = "26.11";
}
