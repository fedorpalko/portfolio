{ pkgs, ... }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    rich
    click
  ]);
in

pkgs.stdenv.mkDerivation {
  pname   = "kelvin-store";
  version = "0.1.0";

  src = ./.;

  buildInputs    = [ pythonEnv ];
  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    install -Dm755 kelvin-store.py $out/libexec/kelvin-store.py
    makeWrapper ${pythonEnv}/bin/python3 $out/bin/kelvin-store \
      --add-flags "$out/libexec/kelvin-store.py"

    # KDE .desktop + icon (shares the main kelvin snowflake icon)
    install -Dm644 ../../assets/kelvin-store.desktop \
      $out/share/applications/kelvin-store.desktop
    install -Dm644 ../../assets/kelvin.svg \
      $out/share/icons/hicolor/scalable/apps/kelvin-store.svg
  '';

  meta = with pkgs.lib; {
    description = "Kelvin Store — Rich TUI for searching and installing nixpkgs packages";
    license     = licenses.mit;
    mainProgram = "kelvin-store";
  };
}
