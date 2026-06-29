{ config, pkgs, lib, kelvinCfg, ... }:

{
  # Konsole — default Kelvin terminal
  programs.konsole = {
    enable         = true;
    defaultProfile = "Kelvin";

    profiles.Kelvin = {
      name        = "Kelvin";
      colorScheme = "Kelvin";
      font = {
        name = "CaskaydiaCove Nerd Font Mono";
        size = 13;
      };
    };
  };

  # Kelvin color scheme for Konsole
  # Written to ~/.local/share/konsole/Kelvin.colorscheme
  xdg.dataFile."konsole/Kelvin.colorscheme".text = ''
    [Background]
    Color=28,28,28

    [BackgroundFaint]
    Color=36,36,36

    [BackgroundIntense]
    Color=42,42,42

    [Color0]
    Color=42,42,42

    [Color0Faint]
    Color=60,60,60

    [Color0Intense]
    Color=80,80,80

    [Color1]
    Color=210,90,90

    [Color1Intense]
    Color=240,100,100

    [Color2]
    Color=120,200,130

    [Color2Intense]
    Color=140,220,150

    [Color3]
    Color=220,185,90

    [Color3Intense]
    Color=240,210,100

    [Color4]
    Color=91,164,207

    [Color4Intense]
    Color=168,216,234

    [Color5]
    Color=150,120,200

    [Color5Intense]
    Color=180,150,230

    [Color6]
    Color=100,190,210

    [Color6Intense]
    Color=168,216,234

    [Color7]
    Color=200,200,200

    [Color7Intense]
    Color=245,245,245

    [Foreground]
    Color=220,220,220

    [ForegroundFaint]
    Color=160,160,160

    [ForegroundIntense]
    Color=245,245,245

    [General]
    Anchor=0.5,0.5
    Blur=false
    ColorRandomization=false
    Description=Kelvin
    FillStyle=Tile
    Opacity=0.95
    Wallpaper=
  '';

  # Konsole global settings
  xdg.configFile."konsolerc".text = ''
    [Desktop Entry]
    DefaultProfile=Kelvin.profile

    [MainWindow]
    MenuBar=Disabled
    StatusBar=Disabled

    [TabBar]
    TabBarPosition=Top
    TabBarVisibility=ShowTabBarWhenNeeded
  '';
}
