{ config, pkgs, lib, ... }:

let cfg = config.kelvin; in

{
  # ── Display server + login manager ────────────────────────────────────────

  services.xserver.enable = true;

  services.desktopManager.plasma6.enable = true;

  services.displayManager.sddm = {
    enable         = true;
    wayland.enable = true;
    # TODO: apply Kelvin SDDM theme once assets/sddm-theme is created
    # theme = "kelvin";
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

  # ── KDE config via plasma-manager (declarative Plasma state) ─────────────
  # TODO: add plasma-manager as flake input and configure:
  #   - panel layout (bottom, centered icons)
  #   - 2 virtual desktops
  #   - default apps
  #   - keyboard shortcuts
  # See: https://github.com/nix-community/plasma-manager

  # ── KDE Wallet — auto-unlock at login ─────────────────────────────────────
  security.pam.services.sddm.enableKwallet = true;
}
