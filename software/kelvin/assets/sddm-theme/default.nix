{ stdenv, lib }:

stdenv.mkDerivation {
  pname   = "sddm-kelvin-theme";
  version = "1.0";
  src     = ./.;

  dontBuild = true;

  installPhase = ''
    runHook preInstall
    mkdir -p $out/share/sddm/themes/kelvin
    cp -r . $out/share/sddm/themes/kelvin/
    runHook postInstall
  '';

  meta = {
    description = "Kelvin SDDM theme — dark blue icy login screen";
    license     = lib.licenses.mit;
  };
}
