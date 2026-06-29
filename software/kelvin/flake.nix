{
  description = "Kelvin — an opinionated NixOS setup that gets out of your way once you're in.";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    nixos-generators = {
      url = "github:nix-community/nixos-generators";
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

  outputs = { self, nixpkgs, home-manager, nixos-generators, disko, plasma-manager, ... }:
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
        { home-manager.sharedModules = [ plasma-manager.homeManagerModules.plasma-manager ]; }
      ];
    };

    # Installer ISO
    packages.${system} = {
      iso = nixos-generators.nixosGenerate {
        inherit system;
        modules = [
          ./options.nix
          ./iso.nix
        ];
        format = "iso";
      };

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
