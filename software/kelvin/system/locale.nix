{ config, pkgs, lib, ... }:

let cfg = config.kelvin; in

{
  time.timeZone = cfg.timezone;

  i18n = {
    defaultLocale = cfg.locale;
    extraLocaleSettings = {
      LC_ADDRESS        = cfg.locale;
      LC_IDENTIFICATION = cfg.locale;
      LC_MEASUREMENT    = cfg.locale;
      LC_MONETARY       = cfg.locale;
      LC_NAME           = cfg.locale;
      LC_NUMERIC        = cfg.locale;
      LC_PAPER          = cfg.locale;
      LC_TELEPHONE      = cfg.locale;
      LC_TIME           = cfg.locale;
    };
  };

  services.xserver.xkb = {
    layout  = cfg.keyboardLayout;
    variant = "";
  };

  # Mirror keyboard layout to virtual console
  console.keyMap =
    if cfg.keyboardLayout == "us" then "us"
    else if cfg.keyboardLayout == "uk" then "uk"
    else cfg.keyboardLayout;
}
