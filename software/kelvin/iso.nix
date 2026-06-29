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
    disko                 # declarative disk partitioning
  ];

  # Auto-login root on tty1. Getty handles the TTY — we hook into the
  # login shell rather than fighting it with a competing systemd unit.
  services.getty.autologinUser = lib.mkForce "root";

  # Launch the installer immediately when root logs in on tty1.
  # Using loginShellInit so it runs after the TTY is fully ready.
  # `exec` replaces the shell — if the installer exits (e.g. user cancels),
  # they drop back to a root shell on tty2+ instead of looping.
  programs.bash.loginShellInit = ''
    if [ "$(tty)" = "/dev/tty1" ]; then
      exec /etc/kelvin-installer/install.sh
    fi
  '';

  # Bundle the installer scripts into the ISO at /etc/kelvin-installer/
  # install.sh derives SCRIPT_DIR from its own path, so sourcing
  # simple.sh / advanced.sh / detect.sh / generate.sh all resolve correctly.
  environment.etc."kelvin-installer" = {
    source = ./installer;
    mode   = "0755";
  };

  # Networking in the live environment
  networking.networkmanager.enable = true;
  networking.wireless.enable       = lib.mkForce false;

  # Allow root SSH during installation (optional, for debugging)
  services.openssh = {
    enable      = true;
    settings.PermitRootLogin = "yes";
  };

  system.stateVersion = "26.11";
}
