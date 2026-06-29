{ config, lib, ... }:

let
  cfg     = config.kelvin;
  compress = lib.optional cfg.zstdCompression "compress=zstd";

  btrfsOpts = subvol:
    [ "subvol=${subvol}" "noatime" ] ++ compress;
in

{
  # Declarative disk layout — managed alongside options.nix.
  # To re-partition (DESTRUCTIVE): sudo disko --mode destroy,format,mount ~/.kelvin/disko.nix
  disko.devices = {
    disk.main = {
      device = cfg.disk;
      type   = "disk";
      content = {
        type = "gpt";
        partitions = {
          ESP = {
            size    = "512M";
            type    = "EF00";
            content = {
              type         = "filesystem";
              format       = "vfat";
              mountpoint   = "/boot";
              mountOptions = [ "umask=0077" ];
            };
          };
          root = {
            size    = "100%";
            content =
              if cfg.filesystem == "btrfs" then {
                type      = "btrfs";
                extraArgs = [ "-L" "nixos" "-f" ];
                subvolumes = {
                  "@"          = { mountpoint = "/";          mountOptions = btrfsOpts "@"; };
                  "@home"      = { mountpoint = "/home";      mountOptions = btrfsOpts "@home"; };
                  "@nix"       = { mountpoint = "/nix";       mountOptions = btrfsOpts "@nix"; };
                  "@snapshots" = { mountpoint = "/.snapshots"; mountOptions = [ "noatime" ]; };
                };
              } else if cfg.filesystem == "ext4" then {
                type       = "filesystem";
                format     = "ext4";
                mountpoint = "/";
              } else {
                type       = "filesystem";
                format     = "xfs";
                mountpoint = "/";
              };
          };
        };
      };
    };
  };
}
