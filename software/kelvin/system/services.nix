{ config, pkgs, lib, ... }:

let cfg = config.kelvin; in

{
  # ── Audio — PipeWire ──────────────────────────────────────────────────────

  services.pipewire = {
    enable            = true;
    alsa.enable       = true;
    alsa.support32Bit = true;
    pulse.enable      = true;
    jack.enable       = true;
    wireplumber.enable = true;
  };
  hardware.pulseaudio.enable = false;
  security.rtkit.enable      = true;

  # ── SSH ───────────────────────────────────────────────────────────────────

  services.openssh = lib.mkIf cfg.services.ssh {
    enable = true;
    settings = {
      PermitRootLogin         = "no";
      PasswordAuthentication  = true;
      X11Forwarding           = false;
    };
    # TODO: once SSH keys are established, set PasswordAuthentication = false
  };

  # ── Printing ──────────────────────────────────────────────────────────────

  services.printing = {
    enable = cfg.services.cups;
    drivers = with pkgs; lib.optionals cfg.services.cups [
      gutenprint
      hplip
    ];
  };

  # ── Bluetooth ─────────────────────────────────────────────────────────────

  hardware.bluetooth = {
    enable      = cfg.services.bluetooth;
    powerOnBoot = cfg.services.bluetooth;
    settings.General.Experimental = "true";
  };
  services.blueman.enable = cfg.services.bluetooth;

  # ── Docker ────────────────────────────────────────────────────────────────

  virtualisation.docker = lib.mkIf cfg.services.docker {
    enable           = true;
    autoPrune.enable = true;
    autoPrune.dates  = "weekly";
  };

  # ── Tailscale ─────────────────────────────────────────────────────────────

  services.tailscale = lib.mkIf cfg.services.tailscale {
    enable     = true;
    useRoutingFeatures = "client";
  };

  # ── Syncthing ─────────────────────────────────────────────────────────────

  services.syncthing = lib.mkIf cfg.services.syncthing {
    enable    = true;
    user      = cfg.username;
    dataDir   = "/home/${cfg.username}";
    configDir = "/home/${cfg.username}/.config/syncthing";
    overrideDevices = false;
    overrideFolders = false;
  };

  # ── fail2ban ──────────────────────────────────────────────────────────────

  services.fail2ban = lib.mkIf cfg.services.fail2ban {
    enable        = true;
    maxretry      = 5;
    ignoreIP      = [ "127.0.0.1/8" "::1" ];
    jails.sshd = ''
      enabled  = true
      port     = ssh
      filter   = sshd
      maxretry = 3
    '';
  };

  # ── Virtualization ────────────────────────────────────────────────────────

  virtualisation.libvirtd = lib.mkIf cfg.useCases.virtualization {
    enable            = true;
    # qemu.ovmf was removed upstream — OVMF images shipped with QEMU are now
    # available by default, so no explicit enable is needed.
    qemu.swtpm.enable = true;
  };
  programs.virt-manager.enable = cfg.useCases.virtualization;
}
