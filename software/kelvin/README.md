# ❄️ Kelvin

> *an opinionated NixOS setup that gets out of your way once you're in.*

Kelvin is a custom NixOS-based personal Linux distribution built on NixOS 26.11 "Zokor" (unstable). It is not a fork — it is a fully declarative, flake-based NixOS configuration with a custom ISO, a personality-driven installer, a curated opinionated app stack, and custom system utilities.

The core promise: grab the ISO, answer some questions, reboot, and you're home. Every app, every zsh alias, every config file — already there.

---

## Philosophy

- **Reproducible** — the entire system is declared in `~/.kelvin/`. One flake, no surprises.
- **Opinionated** — Kelvin has defaults. Strong ones. You can change them, but you don't have to.
- **Approachable** — simple mode holds your hand. Advanced mode assumes you know what BTRFS subvolumes are.
- **Honest** — the installer has a personality. It doesn't pretend to be enterprise software.

---

## Build the ISO

```bash
nix build .#packages.x86_64-linux.iso
```

The ISO lands in `result/`. Flash it to a USB drive:

```bash
sudo dd if=result/iso/kelvin-installer.iso of=/dev/sdX bs=4M status=progress
```

---

## Install

Boot the ISO. The installer launches automatically. Pick Simple or Advanced mode and follow the prompts.

---

## Customize after install

All configuration lives in `~/.kelvin/`. The single source of truth is `~/.kelvin/options.nix`:

```nix
{
  kelvin = {
    hostname     = "my-machine";
    username     = "john";
    timezone     = "Europe/Bratislava";
    kernel       = "zen";
    gpu          = "amd";
    # ... see options.nix for full schema
  };
}
```

After editing, apply changes:

```bash
kelvin update        # pull latest nixpkgs, rebuild
kelvin rollback      # pick a previous generation
kelvin status        # current gen, last update, store size
kelvin clean         # garbage collect old generations
```

Or run the TUI:

```bash
kelvin               # full dashboard
kelvin-store         # search and install packages
```

---

## Repository Structure

```
kelvin/
├── flake.nix              # root — pinned to nixos-unstable (Zokor)
├── options.nix            # full kelvin option schema with defaults
├── configuration.nix      # top-level, imports everything
├── system/                # boot, networking, locale, performance, services
├── hardware/              # GPU, CPU, generated hardware config
├── desktop/               # KDE Plasma, fonts, theme
├── packages.nix           # all packages split by use case
├── home/                  # home-manager: zsh, git
├── installer/             # bash + gum installer scripts
├── tools/kelvin/          # kelvin system manager (python + rich)
├── tools/kelvin-store/    # kelvin store package manager (python + rich)
└── assets/                # boot wallpapers, snowflake SVG
```

---

## Reference

- [DESIGN.md](DESIGN.md) — full design document, installer copy, option schema
- [NixOS 26.11 "Zokor"](https://nixos.org) — the foundation
- [omarchy](https://github.com/basecamp/omarchy) — the inspiration

---

*Kelvin — built on NixOS 26.11 "Zokor". Every BYTE registered.*
