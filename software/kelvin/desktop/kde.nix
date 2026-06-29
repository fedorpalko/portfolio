{ config, pkgs, lib, ... }:

let
  cfg             = config.kelvin;
  kelvinSddmTheme = pkgs.callPackage ../assets/sddm-theme/default.nix {};
in

{
  # ── Display server + login manager ────────────────────────────────────────

  services.xserver.enable = true;

  services.desktopManager.plasma6.enable = true;

  services.displayManager.sddm = {
    enable         = true;
    wayland.enable = true;
    theme          = "kelvin";
  };

  services.displayManager.defaultSession = "plasma";

  # ── Wayland hints ─────────────────────────────────────────────────────────

  environment.sessionVariables = {
    NIXOS_OZONE_WL       = "1";   # Electron apps use Wayland natively
    XDG_SESSION_TYPE     = "wayland";
    MOZ_ENABLE_WAYLAND   = "1";   # Firefox/Floorp
    QT_QPA_PLATFORM      = "wayland;xcb";
    GDK_BACKEND          = "wayland,x11";
  };

  # ── Base KDE applications ─────────────────────────────────────────────────

  environment.systemPackages = with pkgs; [
    kelvinSddmTheme           # Kelvin SDDM login theme
    floorp               # default browser — Firefox fork, less telemetry
    kdePackages.konsole  # default terminal
    kdePackages.kate     # text editor (fallback when VSCode not installed)
    kdePackages.dolphin  # file manager
    kdePackages.ark      # archive manager
    kdePackages.okular   # document viewer
    kdePackages.spectacle # screenshot tool
    kdePackages.kwalletmanager
    kdePackages.kwallet-pam
    libsForQt5.qt5.qtwayland  # Qt5 Wayland support
    qt6.qtwayland             # Qt6 Wayland support
  ];

  # Set Floorp as default browser
  xdg.mime.defaultApplications = {
    "text/html"              = "floorp.desktop";
    "x-scheme-handler/http"  = "floorp.desktop";
    "x-scheme-handler/https" = "floorp.desktop";
    "x-scheme-handler/ftp"   = "floorp.desktop";
  };

  # plasma-manager config lives in home/plasma.nix (home-manager module).
  # It reads kelvinCfg.desktop.{colorScheme,iconPack} to set Plasma theme.

  # ── KDE Wallet — auto-unlock at login ─────────────────────────────────────
  security.pam.services.sddm.enableKwallet = true;
}
