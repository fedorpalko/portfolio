{ config, pkgs, lib, ... }:

let cfg = config.kelvin; in

{
  networking.hostName = cfg.hostname;

  networking.networkmanager.enable = true;
  networking.wireless.enable       = lib.mkForce false; # managed by NetworkManager

  # Firewall — conservative defaults, open ports based on enabled services
  networking.firewall = {
    enable = true;

    allowedTCPPorts =
      lib.optionals cfg.services.ssh [ 22 ]
      ++ lib.optionals cfg.services.syncthing [ 22000 ];

    allowedUDPPorts =
      lib.optionals cfg.services.syncthing [ 22000 21027 ];

    # TODO: open ports for self-hosted services when server use case is enabled
  };

  # DNS via systemd-resolved with fallback to public resolvers
  services.resolved = {
    enable       = true;
    dnssec       = "allow-downgrade";
    domains      = [ "~." ];
    fallbackDns  = [ "1.1.1.1" "9.9.9.9" "2606:4700:4700::1111" ];
  };
}
