{
  description = "Kelvin — an opinionated NixOS setup that gets out of your way once you're in.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    disko = {
      url = "github:nix-community/disko";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    plasma-manager = {
      url = "github:nix-community/plasma-manager";
      inputs.nixpkgs.follows   = "nixpkgs";
      inputs.home-manager.follows = "home-manager";
    };
  };

  outputs = { self, nixpkgs, home-manager, disko, plasma-manager, ... }:
  let
    system = "x86_64-linux";
    pkgs   = nixpkgs.legacyPackages.${system};
  in
  {
    # Full system configuration — used after install
    nixosConfigurations.kelvin = nixpkgs.lib.nixosSystem {
      inherit system;
      modules = [
        ./options.nix
        ./configuration.nix
        ./disko.nix
        home-manager.nixosModules.home-manager
        disko.nixosModules.disko
        { home-manager.sharedModules = [ plasma-manager.homeModules.plasma-manager ]; }
      ];
    };

    # Installer ISO — built with the native nixpkgs ISO image system
    # (nixos-generators was upstreamed/deprecated as of NixOS 25.05). We
    # evaluate a NixOS configuration whose iso.nix imports the native
    # installation-cd module and expose its `system.build.isoImage` output.
    packages.${system} = {
      iso = (nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [
          ./options.nix
          ./iso.nix
        ];
      }).config.system.build.isoImage;

      kelvin       = pkgs.callPackage ./tools/kelvin/default.nix {};
      kelvin-store = pkgs.callPackage ./tools/kelvin-store/default.nix {};
    };

    # Dev shell for working on Kelvin itself
    devShells.${system}.default = pkgs.mkShell {
      buildInputs = with pkgs; [
        gum
        nixos-install-tools
        nix-tree
      ];
    };
  };
}
