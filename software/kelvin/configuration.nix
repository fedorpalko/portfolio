{ config, pkgs, lib, ... }:

let cfg = config.kelvin; in

{
  imports = [
    ./hardware/generated.nix
    ./hardware/gpu.nix
    ./hardware/cpu.nix
    ./system/boot.nix
    ./system/networking.nix
    ./system/locale.nix
    ./system/performance.nix
    ./system/services.nix
    ./desktop/kde.nix
    ./desktop/fonts.nix
    ./desktop/theme.nix
    ./packages.nix
    ./user-packages.nix
  ];

  # Primary user account
  users.users.${cfg.username} = {
    isNormalUser  = true;
    description   = cfg.fullName;
    extraGroups   = [ "wheel" "networkmanager" "audio" "video" ]
      ++ lib.optional cfg.services.docker "docker"
      ++ lib.optional cfg.useCases.virtualization "libvirtd";
    shell = pkgs.zsh;
    # Password is set by the installer via `passwd` after nixos-install
  };

  programs.zsh.enable = true;

  # home-manager wired up — kelvin options passed through extraSpecialArgs
  home-manager = {
    useGlobalPkgs     = true;
    useUserPackages   = true;
    extraSpecialArgs  = { kelvinCfg = cfg; };
    users.${cfg.username} = import ./home/default.nix;
  };

  # Allow unfree packages (NVIDIA drivers, VSCode, Spotify, etc.)
  nixpkgs.config.allowUnfree = true;

  # Nix daemon settings
  nix = {
    settings = {
      experimental-features    = [ "nix-command" "flakes" ];
      auto-optimise-store      = true;
      trusted-users            = [ "root" cfg.username ];
    };
    gc = {
      automatic = true;
      dates     = "weekly";
      options   = "--delete-older-than 14d";
    };
  };

  system.stateVersion = "26.11";
}
