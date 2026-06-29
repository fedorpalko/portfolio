{ config, pkgs, lib, kelvinCfg, ... }:

{
  imports = [
    ./zsh.nix
    ./git.nix
    ./starship.nix
    ./konsole.nix
  ];

  home.username    = kelvinCfg.username;
  home.homeDirectory = "/home/${kelvinCfg.username}";
  home.stateVersion  = "26.11";

  home.packages = with pkgs; [
    btop
    eza
    fzf
    ripgrep
    bat
    fd
    zoxide
    fastfetch
  ];

  # Let home-manager manage itself
  programs.home-manager.enable = true;

  # XDG directories
  xdg.enable = true;
  xdg.userDirs = {
    enable        = true;
    createDirectories = true;
  };

  # Session variables
  home.sessionVariables = {
    EDITOR  = if kelvinCfg.useCases.development then "code" else "kate";
    VISUAL  = "$EDITOR";
    PAGER   = "bat --paging=always";
    MANPAGER = "bat -l man";
  };
}
