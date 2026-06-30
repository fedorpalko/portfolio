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

  # Bake the Kelvin NixOS module tree into the ISO at /etc/kelvin/. During
  # install, generate.sh's _copy_kelvin_modules() looks for /etc/kelvin FIRST and
  # copies these into ~/.kelvin/. Without this, the module tree never reaches the
  # ISO, so nothing gets copied and nixos-install fails with
  #   error: path '/mnt/nix/store/<hash>-source/configuration.nix' does not exist
  # (configuration.nix is simply the first import the generated flake trips on;
  # options.nix survives only because the installer generates it fresh).
  #
  # Every path flake.nix imports — directly (./options.nix, ./configuration.nix,
  # ./disko.nix) and transitively via configuration.nix (system/, hardware/,
  # desktop/, home/, packages.nix, user-packages.nix) — must appear here AND in
  # the copy list in _copy_kelvin_modules(). assets/ is bundled for completeness
  # (themes, icons).
  #
  # options.nix is the option DECLARATIONS module (options.kelvin = mkOption ...);
  # it MUST be baked and copied, otherwise config.kelvin does not exist and
  # nixos-install fails with "attribute 'kelvin' missing". The installer writes
  # the per-machine VALUES into a separate settings.nix (not baked). flake.nix and
  # flake.lock are also generated per-machine and intentionally not baked.
  #
  # Paths are listed individually rather than baking `./.` on purpose: the repo
  # root contains a `result` symlink to the built ISO and flake.lock/iso.nix,
  # none of which belong in the image.
  environment.etc."kelvin/options.nix".source       = ./options.nix;
  environment.etc."kelvin/configuration.nix".source = ./configuration.nix;
  environment.etc."kelvin/disko.nix".source         = ./disko.nix;
  environment.etc."kelvin/packages.nix".source      = ./packages.nix;
  environment.etc."kelvin/user-packages.nix".source = ./user-packages.nix;
  environment.etc."kelvin/system".source            = ./system;
  environment.etc."kelvin/hardware".source          = ./hardware;
  environment.etc."kelvin/desktop".source           = ./desktop;
  environment.etc."kelvin/home".source              = ./home;
  environment.etc."kelvin/assets".source            = ./assets;

  # Enable flakes in the LIVE installer environment. Both `disko` and
  # `nixos-install --flake ...` shell out to `nix` with flake-based commands, so
  # without these experimental features the installer fails at partitioning with
  # "experimental Nix feature 'nix-command'/'flakes' is disabled". (This is the
  # live ISO's nix config; the installed system gets its own from the generated
  # flake.)
  nix.settings.experimental-features = [ "nix-command" "flakes" ];

  # Make `<nixpkgs>` resolvable in the live installer. The installer partitions
  # by running `disko --mode ... /tmp/kelvin-disko.nix` on a *plain* (non-flake)
  # disko file; disko evaluates that file with `nix-instantiate`, which needs
  # `<nixpkgs>` on the Nix search path. A flake-based ISO sets no channels, so
  # NIX_PATH is empty and partitioning fails with:
  #   error: file 'nixpkgs' was not found in the Nix search path
  # Pin it to the exact nixpkgs the ISO was built from (pkgs.path) so evaluation
  # is hermetic and matches the rest of the system.
  nix.nixPath = [ "nixpkgs=${pkgs.path}" ];

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
