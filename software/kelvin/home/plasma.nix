{ lib, kelvinCfg, ... }:

let
  scheme = kelvinCfg.desktop.colorScheme;
  isDark = scheme == "orchis-dark" || scheme == "breeze-dark" || scheme == "nordic";

  # KDE color scheme (kdeglobals ColorScheme / *.colors file name).
  colorSchemeMap = {
    "orchis-dark"  = "OrchisDark";
    "orchis-light" = "Orchis";
    "breeze-dark"  = "BreezeDark";
    "breeze-light" = "BreezeLight";
    "nordic"       = "Nordic";
  };

  # Global theme (Look-and-Feel package id). Only Orchis + Breeze ship a reliable
  # LnF id; nordic has none we can depend on, so it's left to colorScheme alone.
  lookAndFeelMap = {
    "orchis-dark"  = "com.github.vinceliuice.Orchis-dark";
    "orchis-light" = "com.github.vinceliuice.Orchis";
    "breeze-dark"  = "org.kde.breezedark.desktop";
    "breeze-light" = "org.kde.breeze.desktop";
  };

  # Plasma desktop theme (panels/plasmoids).
  plasmaThemeMap = {
    "orchis-dark"  = "Orchis-dark";
    "orchis-light" = "Orchis";
    "breeze-dark"  = "breeze-dark";
    "breeze-light" = "default";
  };

  # Aurorae window decoration, referenced as __aurorae__svg__<theme>.
  auroraeMap = {
    "orchis-dark"  = "__aurorae__svg__Orchis-dark";
    "orchis-light" = "__aurorae__svg__Orchis";
  };

  iconThemeMap = {
    "papirus-dark"  = "Papirus-Dark";
    "papirus-light" = "Papirus-Light";
    "breeze"        = "Breeze";
    "oxygen"        = "Oxygen";
    "tela"          = "Tela";
  };

  # Maps the kelvin font choice to the family name KDE uses for its UI. Kept in
  # sync with the fontconfig sansSerif families in desktop/fonts.nix. google-sans
  # is a legacy alias for Inter.
  fontFamilyMap = {
    "inter"        = "Inter";
    "google-sans"  = "Inter";
    "ibm-plex"     = "IBM Plex Sans";
    "noto"         = "Noto Sans";
    "caskaydia"    = "CaskaydiaCove Nerd Font";
  };
  uiFont = fontFamilyMap.${kelvinCfg.desktop.font} or "Inter";

  lookAndFeel = lookAndFeelMap.${scheme} or null;
  aurorae     = auroraeMap.${scheme} or null;
in

{
  programs.plasma = {
    enable = true;

    workspace = {
      # Full Orchis (or Breeze) look: global theme + colors + plasma theme +
      # window decorations, so the desktop actually matches the chosen theme
      # instead of silently falling back to Breeze.
      colorScheme = colorSchemeMap.${scheme} or "BreezeDark";
      theme       = plasmaThemeMap.${scheme} or "breeze-dark";
      iconTheme   = iconThemeMap.${kelvinCfg.desktop.iconPack} or "Papirus-Dark";

      cursor = {
        theme = "Bibata-Modern-Classic";
        size  = 24;
      };
    }
    # Only set the global theme when we have a real Look-and-Feel id for it —
    # applying a bogus id would error. Applied after colorScheme so Orchis's
    # own colors land.
    // lib.optionalAttrs (lookAndFeel != null) { lookAndFeel = lookAndFeel; }
    // lib.optionalAttrs (aurorae != null) {
      windowDecorations = {
        library = "org.kde.kwin.aurorae";
        theme   = aurorae;
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
        # Subtle translucency + blur for a modern look.
        blur.enable                = true;
        minimization.animation     = "magiclamp";
      };
    };

    # Bottom panel — floating, centered task icons.
    panels = [
      {
        location = "bottom";
        floating  = true;
        height    = 46;
        widgets   = [
          { name = "org.kde.plasma.kickoff"; }
          { name = "org.kde.plasma.pager"; }
          { name = "org.kde.plasma.icontasks"; }
          { name = "org.kde.plasma.marginseparator"; }
          { name = "org.kde.plasma.systemtray"; }
          { name = "org.kde.plasma.digitalclock"; }
          { name = "org.kde.plasma.showdesktop"; }
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
        "Overview"                        = [ "Meta+W" ];
        "Show Desktop"                    = [ "Meta+D" ];
      };
      "org.kde.krunner.desktop" = {
        "_launch" = [ "Meta+Space" "Alt+F2" ];
      };
      "org.kde.spectacle.desktop" = {
        "RectangularRegionCapture" = [ "Meta+Shift+S" ];
      };
    };

    # System UI fonts. Without this block Plasma falls back to Noto Sans
    # regardless of the fontconfig default, so the chosen Kelvin font never
    # actually showed up. Fixed-width always stays on the mono nerd font.
    fonts = {
      general     = { family = uiFont; pointSize = 10; };
      menu        = { family = uiFont; pointSize = 10; };
      toolbar     = { family = uiFont; pointSize = 10; };
      windowTitle = { family = uiFont; pointSize = 10; };
      small       = { family = uiFont; pointSize = 8; };
      fixedWidth  = { family = "CaskaydiaCove Nerd Font Mono"; pointSize = 10; };
    };

    # Plasma system settings tweaks.
    configFile = {
      "kdeglobals" = {
        "KDE"."SingleClick"            = false;
        "KDE"."AnimationDurationFactor" = 0.5;   # snappier animations
        # NumLock on at login (0 = on, 1 = off, 2 = unchanged).
        "Keyboard"."NumLock"           = 0;
      };
      "kwinrc" = {
        "Desktops"."Rows"              = 1;
        # Enable "Present Windows" / Overview hot corner (top-left).
        "Effect-overview"."BorderActivate" = 9;
      };
      "kscreenlockerrc" = {
        "Daemon"."Timeout"      = 10;
        "Daemon"."LockGrace"    = 5;
        "Daemon"."LockOnResume" = true;
      };
      # 24-hour clock + show seconds off by default is fine; keep the panel clean.
      "plasma-localerc"."Formats"."LANG" = kelvinCfg.locale;
      # Dolphin niceties.
      "dolphinrc"."General"."ShowFullPath"          = true;
      "dolphinrc"."General"."RememberOpenedTabs"    = false;
      "dolphinrc"."DetailsMode"."PreviewSize"       = 32;
    };
  };
}
