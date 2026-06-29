{ config, pkgs, lib, ... }:

let cfg = config.kelvin; in

{
  # OpenGL/Vulkan — always enabled; extra packages depend on GPU vendor
  # NOTE: In NixOS 26+ this may be hardware.graphics.* instead of hardware.opengl.*
  hardware.opengl = {
    enable         = true;
    driSupport32Bit = true;

    extraPackages = with pkgs;
      if cfg.gpu == "amd" then [
        amdvlk
        rocm-opencl-icd
        rocm-opencl-runtime
      ]
      else if cfg.gpu == "intel" then [
        intel-media-driver      # VAAPI for recent Intel (Broadwell+)
        vaapiIntel              # older Intel
        vaapiVdpau
        libvdpau-va-gl
      ]
      else [];

    extraPackages32 = with pkgs;
      lib.optionals (cfg.gpu == "amd") [ driversi686Linux.amdvlk ];
  };

  # NVIDIA — proprietary driver stack
  hardware.nvidia = lib.mkIf (cfg.gpu == "nvidia") {
    modesetting.enable       = true;
    powerManagement.enable   = false;
    powerManagement.finegrained = false;
    open             = false;   # use proprietary, not open kernel module
    nvidiaSettings   = true;
    package          = config.boot.kernelPackages.nvidiaPackages.stable;
  };

  services.xserver.videoDrivers = lib.mkIf (cfg.gpu == "nvidia") [ "nvidia" ];

  # Vulkan ICD for AMD
  environment.systemPackages = lib.optionals (cfg.gpu == "amd") (with pkgs; [
    vulkan-tools
    vulkan-loader
    vulkan-validation-layers
  ]);

  # VA-API / VDPAU environment hints for media players
  environment.sessionVariables = lib.mkIf (cfg.gpu == "amd") {
    VDPAU_DRIVER = "radeonsi";
    LIBVA_DRIVER_NAME = "radeonsi";
  };
}
