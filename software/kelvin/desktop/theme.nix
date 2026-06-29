{ config, pkgs, lib, ... }:

let cfg = config.kelvin; in

{
  environment.systemPackages = with pkgs; [
    papirus-icon-theme   # papirus-dark + papirus-light
    tela-icon-theme      # tela
    bibata-cursors       # clean cursor theme
    # breeze + oxygen are shipped with KDE — no separate package needed

    # Color schemes
    # orchis-dark: TODO — not yet in nixpkgs; may need an overlay or manual install
    # nordic: available in nixpkgs as nordic
  ] ++ lib.optional (cfg.desktop.colorScheme == "nordic") pkgs.nordic;

  # Icon pack selection — applied via plasma-manager (see kde.nix TODO)
  # cfg.desktop.iconPack maps to:
  #   papirus-dark  → "Papirus-Dark"
  #   papirus-light → "Papirus-Light"
  #   breeze        → "Breeze"
  #   oxygen        → "Oxygen"
  #   tela          → "Tela"

  # Color scheme selection — applied via plasma-manager (see kde.nix TODO)
  # cfg.desktop.colorScheme maps to:
  #   orchis-dark  → "OrchisDark"   (requires overlay)
  #   breeze-dark  → "BreezeDark"
  #   breeze-light → "BreezeLight"
  #   nordic       → "Nordic"

  # Cursor — Bibata Modern Classic at 24px
  # TODO: set via plasma-manager once wired up
  # programs.plasma.cursors.theme = "Bibata-Modern-Classic";
  # programs.plasma.cursors.size  = 24;

  # GTK theming — so GTK apps match Plasma
  programs.dconf.enable = true;
  environment.sessionVariables.GTK_THEME = lib.mkIf
    (cfg.desktop.colorScheme == "breeze-dark" || cfg.desktop.colorScheme == "orchis-dark")
    "Breeze-Dark";
}
