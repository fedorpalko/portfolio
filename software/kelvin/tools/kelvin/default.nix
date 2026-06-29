{ pkgs, ... }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    rich
    click
  ]);
in

pkgs.stdenv.mkDerivation {
  pname   = "kelvin";
  version = "0.1.0";

  src = ./.;

  buildInputs = [ pythonEnv ];
  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    install -Dm755 kelvin.py $out/libexec/kelvin.py
    makeWrapper ${pythonEnv}/bin/python3 $out/bin/kelvin \
      --add-flags "$out/libexec/kelvin.py"
  '';

  meta = with pkgs.lib; {
    description = "Kelvin system manager — Rich TUI for managing your NixOS install";
    license     = licenses.mit;
    mainProgram = "kelvin";
  };
}
