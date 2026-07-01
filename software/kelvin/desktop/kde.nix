{ config, pkgs, lib, ... }:

let
  cfg             = config.kelvin;
  dm              = cfg.desktop.displayManager;
  kelvinSddmTheme = pkgs.callPackage ../assets/sddm-theme/default.nix {};

  # GTK theme name used by the LightDM GTK greeter, matched to the chosen scheme.
  gtkGreeterTheme =
    if      cfg.desktop.colorScheme == "orchis-dark"  then "Orchis-Dark"
    else if cfg.desktop.colorScheme == "orchis-light" then "Orchis-Light"
    else if cfg.desktop.colorScheme == "breeze-light" then "Breeze"
    else                                                   "Breeze-Dark";
  gtkGreeterIcons =
    if cfg.desktop.iconPack == "papirus-light" then "Papirus-Light" else "Papirus-Dark";
in

{
  # ── Display server + desktop ──────────────────────────────────────────────

  services.xserver.enable = true;
  services.desktopManager.plasma6.enable = true;
  services.displayManager.defaultSession = "plasma";

  # ── Login / display manager (default: ly) ─────────────────────────────────
  # Exactly one is enabled, selected by cfg.desktop.displayManager.

  services.displayManager.ly = lib.mkIf (dm == "ly") {
    enable = true;
    # ly reads config.ini; keep it minimal and known-good so login never breaks.
    settings = {
      clock          = "%c";
      animation      = "matrix";
      hide_borders   = false;
    };
  };

  services.displayManager.sddm = lib.mkIf (dm == "sddm") {
    enable         = true;
    wayland.enable = true;
    theme          = "kelvin";
  };

  services.displayManager.gdm = lib.mkIf (dm == "gdm") {
    enable = true;   # GDM defaults to Wayland on modern nixpkgs
  };

  services.xserver.displayManager.lightdm = lib.mkIf (dm == "lightdm") {
    enable = true;
    greeters.gtk = {
      enable          = true;
      theme.name      = gtkGreeterTheme;
      theme.package   = if lib.hasPrefix "Orchis" gtkGreeterTheme
                        then pkgs.orchis-theme else pkgs.kdePackages.breeze-gtk;
      iconTheme.name    = gtkGreeterIcons;
      iconTheme.package = pkgs.papirus-icon-theme;
      cursorTheme.name    = "Bibata-Modern-Classic";
      cursorTheme.package = pkgs.bibata-cursors;
    };
  };

  services.greetd = lib.mkIf (dm == "greetd") {
    enable = true;
    settings.default_session = {
      command = "${lib.getExe pkgs.tuigreet} --time --remember --asterisks --cmd startplasma-wayland";
      user    = "greeter";
    };
  };

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
    floorp-bin           # default browser — Firefox fork, less telemetry
    kdePackages.konsole  # default terminal
    kdePackages.kate     # text editor (fallback when VSCode not installed)
    kdePackages.dolphin  # file manager
    kdePackages.ark      # archive manager
    kdePackages.okular   # document viewer
    kdePackages.spectacle # screenshot tool
    kdePackages.kwalletmanager
    kdePackages.kwallet-pam
    qt5.qtwayland  # Qt5 Wayland support
    qt6.qtwayland  # Qt6 Wayland support
  ]
  ++ lib.optional (dm == "sddm")   kelvinSddmTheme   # Kelvin SDDM login theme
  ++ lib.optional (dm == "greetd") tuigreet;

  # Set Floorp as default browser
  xdg.mime.defaultApplications = {
    "text/html"              = "floorp.desktop";
    "x-scheme-handler/http"  = "floorp.desktop";
    "x-scheme-handler/https" = "floorp.desktop";
    "x-scheme-handler/ftp"   = "floorp.desktop";
  };

  # plasma-manager config lives in home/plasma.nix (home-manager module).
  # It reads kelvinCfg.desktop.{colorScheme,iconPack,font} to set the Plasma
  # global theme, colors, icons, window decorations and fonts.

  # ── KDE Wallet — auto-unlock at login for the active greeter ───────────────
  security.pam.services = lib.mkMerge [
    (lib.mkIf (dm == "sddm") { sddm.enableKwallet = true; })
    (lib.mkIf (dm == "ly")   { ly.enableKwallet   = true; })
  ];
}
