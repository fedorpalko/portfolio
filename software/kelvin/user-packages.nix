# ~/.kelvin/user-packages.nix
# Packages installed via kelvin-store.
# This file is managed automatically — add/remove packages with `kelvin-store`.
# You can also hand-edit it; run `kelvin update` after any manual changes.
{ pkgs, ... }:

{
  environment.systemPackages = with pkgs; [
    # KELVIN-STORE-BEGIN
    # KELVIN-STORE-END
  ];
}
