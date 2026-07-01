{ autoinstallScript }:

{ config, pkgs, lib, modulesPath, ... }:

# TEST-ONLY ISO overlay (parametrized). Imports the real installer ISO unchanged
# (../iso.nix) and layers on top:
#   * a serial console so a headless QEMU run can be read from a log file,
#   * a oneshot systemd service that runs the non-interactive autoinstall,
#   * binary-cache substituters so nixos-install pulls the prebuilt closure from
#     the host (10.0.2.2 over QEMU user-net) instead of recompiling under TCG.
#
# `autoinstallScript` selects WHICH non-interactive installer to bake — the
# simple-mode harness (test/autoinstall.sh) or the advanced-mode one
# (test/autoinstall-advanced.sh). Both reuse the exact generate.sh functions the
# real interactive installer uses; only the fixed answers + code path differ.
#
# The shipped `packages.iso` output is NOT affected — these are separate
# `iso-test*` packages. The install logic under test (the baked ./installer
# scripts and the Kelvin module tree) is byte-for-byte the same as what ships.

{
  imports = [ ../iso.nix ];

  # Serial console: send kernel + systemd console output to ttyS0 so QEMU's
  # `-serial file:` captures everything headlessly. Keep tty0 too (last console=
  # wins for /dev/console, so ttyS0 is last → /dev/console == serial).
  boot.kernelParams = [ "console=tty0" "console=ttyS0,115200" ];

  # Bake the selected test autoinstaller onto the ISO.
  environment.etc."kelvin-autoinstall.sh" = {
    source = autoinstallScript;
    mode   = "0755";
  };

  # Run the non-interactive install automatically once the system is up.
  systemd.services.kelvin-autoinstall = {
    description   = "Kelvin non-interactive test install";
    wantedBy      = [ "multi-user.target" ];
    after         = [ "network-online.target" "getty.target" ];
    wants         = [ "network-online.target" ];
    serviceConfig = {
      Type             = "oneshot";
      RemainAfterExit  = true;
      StandardOutput   = "journal+console";
      StandardError    = "journal+console";
      # Run it in a LOGIN shell (`bash --login`) so it sources /etc/profile and
      # /etc/set-environment — giving it the same PATH and NIX_PATH the real
      # interactive installer gets from its tty1 login shell. Without --login a
      # systemd service has neither, so `disko` can't find `<nixpkgs>` (which the
      # installer relies on via nix.nixPath) and partitioning fails. This keeps
      # the test faithful to the real install environment.
      ExecStart        = "${pkgs.bash}/bin/bash --login /etc/kelvin-autoinstall.sh";
      TimeoutStartSec  = "infinity";
    };
  };

  # Pull the prebuilt system closure from the host's binary cache (served over
  # HTTP at 10.0.2.2:8000 by test-iso.sh via QEMU user networking). Fall back to
  # the public cache for anything the host cache is missing. require-sigs is off
  # because the host cache is unsigned; this is a throwaway test ISO.
  nix.settings = {
    substituters = lib.mkForce [
      "http://10.0.2.2:8000"
      "https://cache.nixos.org"
    ];
    trusted-substituters = [ "http://10.0.2.2:8000" ];
    require-sigs = false;
  };
}
