{ lib, kelvinCfg, ... }:

let
  colorSchemeMap = {
    "orchis-dark"  = "OrchisDark";
    "breeze-dark"  = "BreezeDark";
    "breeze-light" = "BreezeLight";
    "nordic"       = "Nordic";
  };
  iconThemeMap = {
    "papirus-dark"  = "Papirus-Dark";
    "papirus-light" = "Papirus-Light";
    "breeze"        = "Breeze";
    "oxygen"        = "Oxygen";
    "tela"          = "Tela";
  };
  # Maps the kelvin font choice to the actual family name KDE should use for its
  # UI. Kept in sync with the fontconfig sansSerif families in desktop/fonts.nix.
  # google-sans is a legacy alias for Inter.
  fontFamilyMap = {
    "inter"        = "Inter";
    "google-sans"  = "Inter";
    "ibm-plex"     = "IBM Plex Sans";
    "noto"         = "Noto Sans";
    "caskaydia"    = "CaskaydiaCove Nerd Font";
  };
  uiFont = fontFamilyMap.${kelvinCfg.desktop.font} or "Inter";
in

{
  programs.plasma = {
    enable = true;

    workspace = {
      colorScheme = colorSchemeMap.${kelvinCfg.desktop.colorScheme} or "BreezeDark";
      iconTheme   = iconThemeMap.${kelvinCfg.desktop.iconPack}     or "Papirus-Dark";
      cursor = {
        theme = "Breeze";
        size  = 24;
      };
    };

    # System UI fonts. Without this block Plasma falls back to its built-in
    # default (Noto Sans) regardless of the fontconfig default, so the chosen
    # Kelvin font never actually showed up in the desktop. General/menu/toolbar/
    # title/small use the chosen sans; fixed-width always stays on the mono nerd
    # font so terminals and code stay monospaced.
    fonts = {
      general     = { family = uiFont; pointSize = 10; };
      menu        = { family = uiFont; pointSize = 10; };
      toolbar     = { family = uiFont; pointSize = 10; };
      windowTitle = { family = uiFont; pointSize = 10; };
      small       = { family = uiFont; pointSize = 8; };
      fixedWidth  = { family = "CaskaydiaCove Nerd Font Mono"; pointSize = 10; };
    };

    kwin = {
      virtualDesktops = {
        number = 2;
        names  = [ "Main" "Work" ];
      };
      effects = {
        desktopSwitching.animation = "slide";
        wobblyWindows.enable       = true;
      };
      # Disable compositing effects that hurt gaming
      nightLight.enable = false;
    };

    # Bottom panel — centered task icons, floating style
    panels = [
      {
        location = "bottom";
        floating  = true;
        height    = 44;
        widgets   = [
          { name = "org.kde.plasma.kickoff"; }
          { name = "org.kde.plasma.pager"; }
          { name = "org.kde.plasma.icontasks"; }
          { name = "org.kde.plasma.marginseparator"; }
          { name = "org.kde.plasma.systemtray"; }
          { name = "org.kde.plasma.digitalclock"; }
        ];
      }
    ];

    shortcuts = {
      kwin = {
        "Switch One Desktop to the Left"  = [ "Meta+Left"  "Ctrl+F1" ];
        "Switch One Desktop to the Right" = [ "Meta+Right" "Ctrl+F2" ];
        "Window Maximize"                 = [ "Meta+Up" ];
        "Window Minimize"                 = [ "Meta+Down" ];
        "Window Quick Tile Left"          = [ "Meta+Shift+Left" ];
        "Window Quick Tile Right"         = [ "Meta+Shift+Right" ];
      };
      "org.kde.krunner.desktop" = {
        "_launch" = [ "Meta+Space" "Alt+F2" ];
      };
    };

    # Plasma system settings tweaks
    configFile = {
      "kdeglobals" = {
        "KDE" = {
          "SingleClick" = false;
        };
      };
      "kscreenlockerrc" = {
        "Daemon" = {
          "Timeout"            = 10;
          "LockGrace"          = 5;
          "LockOnResume"       = true;
        };
      };
    };
  };
}
