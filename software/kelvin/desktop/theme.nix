{ config, pkgs, lib, ... }:

let
  cfg     = config.kelvin;
  scheme  = cfg.desktop.colorScheme;
  isDark  = scheme == "orchis-dark" || scheme == "breeze-dark" || scheme == "nordic";
  isOrchis = scheme == "orchis-dark" || scheme == "orchis-light";

  orchis-kde = pkgs.callPackage ../assets/orchis-kde/default.nix {};
in

{
  environment.systemPackages = with pkgs; [
    papirus-icon-theme   # papirus-dark + papirus-light
    tela-icon-theme      # tela
    bibata-cursors       # clean cursor theme (Bibata-Modern-Classic)
    orchis-kde           # Orchis for KDE: color schemes, global themes, aurorae, Kvantum
    orchis-theme         # Orchis GTK theme (so GTK apps match Plasma)
    # breeze + oxygen ship with KDE — no separate package needed
  ] ++ lib.optional (scheme == "nordic") pkgs.nordic;

  # GTK theming — so GTK apps match Plasma. Orchis themes are named
  # Orchis-Dark / Orchis-Light; Breeze schemes fall back to Breeze GTK.
  programs.dconf.enable = true;
  environment.sessionVariables.GTK_THEME =
    if      scheme == "orchis-dark"  then "Orchis-Dark"
    else if scheme == "orchis-light" then "Orchis-Light"
    else if isDark                   then "Breeze-Dark"
    else                                  "Breeze";
}
