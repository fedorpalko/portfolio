{ config, pkgs, lib, ... }:

let cfg = config.kelvin; in

{
  fonts = {
    enableDefaultPackages = true;

    packages = with pkgs; [
      # CaskaydiaCove Nerd Font — terminal, code, Kelvin logo wordmark
      nerd-fonts.caskaydia-cove

      # Google Sans (Product Sans) — not freely redistributable; using Inter as
      # the closest open-source match. TODO: replace with a properly licensed
      # Google Sans-compatible font if/when one becomes available.
      inter

      # Alternatives
      ibm-plex             # IBM Plex Sans / Mono / Serif
      noto-fonts           # broad Unicode coverage
      noto-fonts-cjk-sans
      noto-fonts-color-emoji
      liberation_ttf       # metric-compatible Arial / Times / Courier
    ];

    fontconfig = {
      enable = true;

      defaultFonts = {
        sansSerif =
          if      cfg.desktop.font == "google-sans" then [ "Inter" "Noto Sans" ]
          else if cfg.desktop.font == "caskaydia"   then [ "CaskaydiaCove Nerd Font" "Noto Sans" ]
          else if cfg.desktop.font == "ibm-plex"    then [ "IBM Plex Sans" "Noto Sans" ]
          else                                           [ "Noto Sans" ];

        serif =
          if cfg.desktop.font == "ibm-plex" then [ "IBM Plex Serif" "Noto Serif" ]
          else [ "Noto Serif" ];

        monospace = [ "CaskaydiaCove Nerd Font Mono" "Noto Sans Mono" ];
        emoji     = [ "Noto Color Emoji" ];
      };

      # Subpixel rendering — suits modern LCD and OLED screens
      antialias    = true;
      hinting.enable = true;
      hinting.style = "slight";
      subpixel.rgba = "rgb";
    };
  };
}
