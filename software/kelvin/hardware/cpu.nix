{ config, pkgs, lib, ... }:

let cfg = config.kelvin; in

{
  hardware.enableRedistributableFirmware = true;

  hardware.cpu.amd.updateMicrocode =
    lib.mkIf (cfg.cpu == "amd") (lib.mkDefault true);

  hardware.cpu.intel.updateMicrocode =
    lib.mkIf (cfg.cpu == "intel") (lib.mkDefault true);

  # AMD P-state driver — better power management on Zen 3+ (Ryzen 5000+)
  boot.kernelParams = lib.mkIf (cfg.cpu == "amd") [
    "amd_pstate=active"
  ];

  # Intel P-state driver — for 12th gen+ (Alder Lake+)
  # boot.kernelParams = lib.mkIf (cfg.cpu == "intel") [
  #   "intel_pstate=active"
  # ];

  # auto-detect: cpuid at boot will handle microcode loading for either vendor
  # when cfg.cpu == "auto", both updateMicrocode options are false above and
  # NixOS will include both AMD and Intel microcode packages via redistributable firmware
}
