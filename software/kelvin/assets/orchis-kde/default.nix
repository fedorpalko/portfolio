{ lib, stdenvNoCC, fetchFromGitHub }:

# Orchis theme for KDE Plasma — packaged from vinceliuice/Orchis-kde, which is
# NOT in nixpkgs (nixpkgs only ships the GTK `orchis-theme`). Provides the real
# Plasma color schemes, Aurorae window decorations, desktop themes, global themes
# (Look-and-Feel), Kvantum themes and wallpapers, laid out under $out/share so
# NixOS aggregates them into XDG_DATA_DIRS. Mirrors upstream install.sh.
#
# Identifiers this exposes (referenced from home/plasma.nix):
#   color schemes    : Orchis (light), OrchisDark (dark)
#   global themes    : com.github.vinceliuice.Orchis (light),
#                      com.github.vinceliuice.Orchis-dark (dark)
#   aurorae themes   : Orchis (light), Orchis-dark (dark)
#   desktop themes   : Orchis (light), Orchis-dark (dark)

stdenvNoCC.mkDerivation (finalAttrs: {
  pname   = "orchis-kde";
  version = "0-unstable-2025-04";

  src = fetchFromGitHub {
    owner = "vinceliuice";
    repo  = "Orchis-kde";
    rev   = "b2a96919eee40264e79db402b915f926436100ad";
    hash  = "sha256-mO1AVrnXNdg3Rftj0cQWef/RrBgSDy5kaMHagwKywEo=";
  };

  dontConfigure = true;
  dontBuild     = true;

  installPhase = ''
    runHook preInstall

    # Plasma color schemes
    install -d $out/share/color-schemes
    cp -r color-schemes/*.colors $out/share/color-schemes/

    # Aurorae window decorations
    install -d $out/share/aurorae/themes
    cp -r aurorae/* $out/share/aurorae/themes/

    # Plasma desktop themes (+ embedded colors, matching upstream install.sh)
    install -d $out/share/plasma/desktoptheme
    cp -r plasma/desktoptheme/Orchis      $out/share/plasma/desktoptheme/
    cp -r plasma/desktoptheme/Orchis-dark $out/share/plasma/desktoptheme/
    cp -r plasma/desktoptheme/icons       $out/share/plasma/desktoptheme/Orchis/
    cp -r plasma/desktoptheme/icons       $out/share/plasma/desktoptheme/Orchis-dark/
    cp color-schemes/Orchis.colors        $out/share/plasma/desktoptheme/Orchis/colors
    cp color-schemes/OrchisDark.colors    $out/share/plasma/desktoptheme/Orchis-dark/colors

    # Global themes (Look-and-Feel)
    install -d $out/share/plasma/look-and-feel
    cp -r plasma/look-and-feel/* $out/share/plasma/look-and-feel/

    # Kvantum (for Qt apps that use it)
    install -d $out/share/Kvantum
    cp -r Kvantum/* $out/share/Kvantum/

    # Wallpapers
    install -d $out/share/wallpapers
    cp -r wallpaper/* $out/share/wallpapers/

    runHook postInstall
  '';

  meta = {
    description = "Orchis theme for KDE Plasma (color schemes, Aurorae, global themes, Kvantum)";
    homepage    = "https://github.com/vinceliuice/Orchis-kde";
    license     = lib.licenses.gpl3Only;
    platforms   = lib.platforms.all;
  };
})
