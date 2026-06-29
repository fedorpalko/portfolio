{ config, pkgs, lib, modulesPath, ... }:

{
  imports = [
    "${modulesPath}/installer/cd-dvd/installation-cd-minimal.nix"
  ];

  # Name the image. `isoImage.isoName` was renamed to `image.fileName` in
  # NixOS 25.05 (the old name is now only a deprecated alias). We drive it
  # through `image.baseName` so every derived path stays consistent:
  #   image.fileName -> "kelvin-installer.iso"      (baseName + ".iso")
  #   image.filePath -> "iso/kelvin-installer.iso"
  #   store path / on-disk file -> kelvin-installer.iso
  # Setting only image.fileName would rename the symlink target but leave the
  # actual ISO file named "nixos-...", so we set baseName instead. The default
  # baseName also embeds isoImage.edition ("minimal"), which is what produced
  # the misleading "nixos-minimal-*.iso" name previously.
  image.baseName = lib.mkForce "kelvin-installer";

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
  #
  # Run it as a CHILD of the login shell — do NOT `exec`. With `exec`, the
  # installer replaced the login shell, so the moment it exited for *any* reason
  # (a failed install step, an error handler's shell hitting EOF, or the user
  # choosing to stay in the live environment) the session ended and getty
  # auto-relaunched the installer — which looked exactly like the installer
  # "looping back to the start", far too fast to read any error.
  #
  # Running it as a child keeps this login shell alive as a safety net: when the
  # installer exits, control returns here and we drop to an interactive root
  # prompt with whatever the installer left on screen still visible.
  programs.bash.loginShellInit = ''
    if [ "$(tty)" = "/dev/tty1" ]; then
      /etc/kelvin-installer/install.sh || true
      echo
      echo "The Kelvin installer has exited — you're now at a root shell."
      echo "Re-run it any time with:  /etc/kelvin-installer/install.sh"
      echo
    fi
  '';

  # Bundle the installer scripts into the ISO at /etc/kelvin-installer/.
  # IMPORTANT: do NOT set `mode` here. A non-symlink `mode` makes environment.etc
  # copy/hardlink the entry as a single regular file (non-recursive `cp`), which
  # for a *directory* source leaves /etc/kelvin-installer as a non-directory —
  # so `/etc/kelvin-installer/install.sh` fails with ENOTDIR ("not a directory").
  # With the default symlink mode, /etc/kelvin-installer becomes a symlink to the
  # store directory and the scripts keep their executable bits from the repo.
  # install.sh derives SCRIPT_DIR from its own path (resolving the symlink), so
  # sourcing simple.sh / advanced.sh / detect.sh / generate.sh all resolve.
  environment.etc."kelvin-installer".source = ./installer;

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
