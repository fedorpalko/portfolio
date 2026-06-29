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
