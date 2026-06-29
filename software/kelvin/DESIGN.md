# ❄️ Kelvin — Design Document
> *an opinionated NixOS setup that gets out of your way once you're in.*

---

## 1. Project Overview

Kelvin is a personal NixOS-based operating system built on NixOS 26.11 "Zokor" (unstable). It is not a fork — it is a fully declarative, flake-based NixOS configuration with a custom ISO, a personality-driven installer, a curated opinionated app stack, and custom system utilities. Think omarchy, but on Nix instead of Arch, and with a lot more attitude.

The core promise: grab the ISO, answer some questions, reboot, and you're home. Every app, every zsh alias, every config file — already there. The only thing you change after install is the theme.

### Philosophy
- **Reproducible** — the entire system is declared in `~/.kelvin/`. One flake, no surprises.
- **Opinionated** — Kelvin has defaults. Strong ones. You can change them, but you don't have to.
- **Approachable** — simple mode holds your hand. Advanced mode assumes you know what BTRFS subvolumes are.
- **Honest** — the installer has a personality. It doesn't pretend to be enterprise software.

### Reference Points
- **omarchy** — DHH's opinionated Arch setup. Same energy, better foundation.
- **NixOS** — the only Linux ecosystem where "reproducible personal distro" isn't a cope.

---

## 2. Visual Identity

### Name
**Kelvin** — named after the unit of absolute temperature, playing on the NixOS snowflake logo. Zero pretension. One word. Sounds like a real operating system.

### Tagline
*an opinionated NixOS setup that gets out of your way once you're in.*

### Color Palette

| Name | Hex | Usage |
|------|-----|-------|
| Kelvin Blue | `#A8D8EA` | Simple installer background, boot theme (light), primary accent |
| Kelvin White | `#F5F5F5` | Text on dark, UI elements |
| Kelvin Dark | `#2A2A2A` | Advanced installer background, boot theme (dark) |
| Kelvin Frost | `#E8F4FD` | Simple installer text areas, highlights |
| Kelvin Ice | `#5BA4CF` | Borders, secondary accents, selected states |

### Typography
- **Display / Logo** — CaskaydiaCove Nerd Font Bold (the ❄️ KELVIN wordmark)
- **UI / Body** — Google Sans
- **Terminal / Code** — CaskaydiaCove Nerd Font Mono
- **Installer (TTY)** — system TTY font (no custom fonts available in TTY environment — the installer is designed to look elegant within these constraints)

### The Snowflake Icon
The Kelvin icon is a clean, minimal six-pointed snowflake SVG. Requirements:
- Works at 16px (taskbar), 48px (app menu), 256px (about screen)
- Monochrome version in Kelvin White for dark backgrounds
- Full color version in Kelvin Blue for light backgrounds
- Used on: app menu entries for `kelvin` and `kelvin-store`, boot splash, installer header, README

---

## 3. Installer Design

The installer IS Kelvin. It introduces itself, it has opinions, it has personality. It is written in **bash + gum** (charmbracelet/gum), taking inspiration from the omarchy installer aesthetic.

### Mode Selection

The first real screen after the welcome splash asks one question:

```
How do you want to do this?

  Simple Install    — I'll guide you through everything.
                      Friendly, fast, no jargon.

  Advanced Install  — You know what you're doing.
                      Full control. No hand-holding.
```

Picking Simple keeps the light blue background throughout.  
Picking Advanced immediately shifts the background to Kelvin Dark and the tone changes completely.

---

### 3.1 Simple Mode

**Voice profile:** warm, encouraging, second-person friendly. Celebrates small wins. Never uses jargon without explaining it. Has "I'm not sure" options everywhere. Treats the user like a smart person who just hasn't done this before.

#### Screen 1 — Welcome
```
        ❄️  K E L V I N  ❄️

  Hey, I'm Kelvin, your new computer operating 
  system, and I'm here to help you install me!

  This should only take a few minutes.
  Let's get started!

  [ Let's go! ]
```
*Background: Kelvin Blue. Text: Kelvin White.*

#### Screen 2 — What's this computer for?
```
  First things first — what will you do on this computer?
  Pick everything that applies, don't worry about getting 
  it perfect, you can always add more later!

  [x] Development      code editors, docker, AI tools, Python, Node...
  [ ] Gaming           Steam, Lutris, Proton, game optimizations...
  [ ] Office Work      LibreOffice, email, notes, document stuff...
  [ ] Media            YouTube downloader, video editing, streaming, music...
  [ ] Creative Work    design tools, image editing, illustration...
  [ ] Science & Data   Jupyter, data tools, LaTeX, R...
  [ ] Privacy          VPN tools, encrypted messaging, Tor browser...
  [ ] Server & Hosting docker, portainer, nginx, self-hosting tools...
```
*Multi-select via gum choose --no-limit. Package list shown in dim smaller text under each option.*

#### Screen 3 — About you
```
  Now, a little about you.
  This sets up your account and git configuration.

  What's your name?          [ John Doe            ]
  What's your email?         [ john@example.com    ]
  Pick a username            [ john                ]
  Pick a password            [ ············        ]
  (make sure you can remember it!)
  Confirm password           [ ············        ]
```

#### Screen 4 — Where are you?
```
  Let's set your timezone so your clock is right.
  Start typing to search — there are a lot of options!

  Timezone: [ Europe/Brat... ] 🔍

  Keyboard layout:
    English (US)  ← we recommend this one
    English (UK)
    Slovak
    Czech
    Other...
```
*Timezone uses gum filter for fuzzy search.*

#### Screen 5 — The disk
```
  Which disk should Kelvin go on?
  We'll be wiping it completely, so choose carefully!

  ★  /dev/nvme0n1   Samsung 970 EVO   500GB   ← we recommend this one
     /dev/sda       WD Blue           1TB
     /dev/sdb       USB Drive         32GB

  (we highlighted the one that looks most like a system drive)
```
*Recommends largest non-USB drive or drive with existing OS detected.*

#### Screen 6 — Confirmation
```
  Here's what we're going to do:

  ✓  Install Kelvin on /dev/nvme0n1 (Samsung 970 EVO, 500GB)
  ✓  Create account: john
  ✓  Timezone: Europe/Bratislava
  ✓  Packages: Development, Gaming

  Did you pick the right disk? This will erase everything on it.

  [ Yes, let's go! ]   [ Wait, go back ]
```

#### Screen 7 — Installing
```
        ❄️  K E L V I N  ❄️

  hey, great job. now sit back, grab a drink —
  Kelvin is installing. we'll let you know when 
  it's done.

  ◐  Building system configuration...

  [████████████░░░░░░░░] 61%
```
*gum spin for individual steps. Progress communicated warmly.*

#### Screen 8 — Done
```
        ❄️  K E L V I N  ❄️

  you're all set! Kelvin is installed.
  your computer will restart in a moment.

  welcome home. 🏠

  [ Restart now ]
```

---

### 3.2 Advanced Mode

**Voice profile:** chaotic, roast-heavy, assumes competence. ALL CAPS for dramatic questions. Lowercase sarcasm for contrast. Roasts bad configuration combinations. Has an escape hatch back to simple mode. Still actually helpful — the aggression signals "pay attention, this matters."

#### Screen 1 — Welcome
```
        ❄️  K E L V I N  ❄️

  What's up, I'm Kelvin, install me bitch.
  I want to know everything you put into me.
  Every BYTE will be registered.
  You're on your own lol.

  [ I'm ready. ]          [ actually take me back to simple ]
```
*Background shifts to Kelvin Dark. Same snowflake, different energy.*

#### Screen 2 — Architecture check
```
  ARE WE x86_64?

    x86_64   — yes, normal computer, we can proceed
    aarch64  — ARM. raspberry pi? mac with apple silicon?
               some things won't apply. you know what you're doing.
    Other    — godspeed

  also, IS ANANICY-CPP APPLICABLE FOR YOUR USE CASE?
  (process priority daemon, great for desktop responsiveness, 
   irrelevant if this is a server)

    Yes, I use this as a desktop
    No, skip it
    What's ananicy-cpp?  ← okay maybe simple mode was right for you
```

#### Screen 3 — What's this machine for?
```
  WHAT ARE WE BUILDING HERE.

  [x] Development      vscode, docker, claude code, antigravity, python, node, neovim...
  [ ] Gaming           steam, lutris, gamemode, proton, mangohud, gamescope...
  [ ] Gaming Tweaks    cpu governor switching, cachyos-kernel tweaks, low-latency audio...
  [ ] Office           libreoffice, thunderbird, obsidian...
  [ ] Media            vlc, ffmpeg, yt-dlp, obs, spotify...
  [ ] Creative         kdenlive, gimp, inkscape, krita...
  [ ] Science & Data   jupyter, pandas, R, julia, texlive, gnuplot...
  [ ] Privacy          mullvad, tor browser, signal, protonmail bridge...
  [ ] Server           portainer, nginx, caddy, postgresql, redis...
  [ ] Legacy Hardware  firmware blobs, broadcom wifi, older GPU support, DKMS modules...
  [ ] Virtualization   virt-manager, QEMU, KVM, looking glass...
  [ ] Security         nmap, wireshark, burpsuite, metasploit... (you know what you're doing)

  (pick what applies. we'll roast you if your picks contradict each other later.)
```

#### Screen 4 — About you
```
  who are you. git needs to know.

  name:      [ ]
  email:     [ ]
  username:  [ ]
  password:  [ ]
  hostname:  [ ]   what do you want to call this machine?
```

#### Screen 5 — Bootloader
```
  PICK YOUR BOOTLOADER.

  ❄️  Limine        — recommended. modern, fast, pretty.
                      kelvin themes apply here. this is the move.
                      supports BIOS and UEFI. built in Go.

     systemd-boot   — solid. boring. no themes. works everywhere.
                      UEFI only. if you don't care about aesthetics,
                      or just hate fun.

     GRUB           — legacy. slow. it'll boot anything though.
                      pick this if your machine is from 2009 or
                      you just love pain for some reason.
```

#### Screen 6 — Boot theme (if Limine selected)
```
  BOOTLOADER THEME.
  (you picked limine, good. now make it yours.)

    ❄️ Light    — kelvin blue and white. clean. friendly.
                  looks good. the correct choice.

       Dark     — dark grey and white. serious. mysterious.
                  for people who think light mode is for children.
```

#### Screen 7 — Filesystem
```
  DO YOU WANT BTRFS SUBVOLUMES?

  if you don't know what that means, hit X and go back to simple.
  if you do — yes means snapshots, rollbacks, compression.
  obviously the correct answer is yes.

    BTRFS with subvolumes   ← DO THIS
    ext4                    — okay. coward. but okay.
    XFS                     — interesting choice. respected.

  SWAP CONFIGURATION:
    zram only (recommended) — fast, RAM-based, no swap partition
    zram + swapfile         — specify size: [ 4 ] GB
    swapfile only           — why
    none                    — you're on your own if you OOM
```

#### Screen 8 — Disk and partitioning
```
  PICK THE DISK. THIS WIPES IT.

     /dev/nvme0n1   Samsung 970 EVO   500GB
     /dev/sda       WD Blue           1TB
     /dev/sdb       USB Drive         32GB

  PARTITION SCHEME:
    Auto (recommended)   — EFI 512MB, root takes the rest
    Manual               — you specify sizes. you know the risks.

  ZSTD COMPRESSION? (btrfs only)
    Yes    — smaller disk usage, negligible CPU overhead. yes.
    No     — leaving performance on the table, but it's your life.
```

#### Screen 9 — Hardware
```
  CPU MANUFACTURER?

    AMD      — good taste
    Intel    — respectable
    IDK      — we'll figure it out  (runs lscpu)

  GPU SITUATION?

    AMD      — excellent. open source drivers. the way.
    NVIDIA   — respect. we'll make it work. proprietary drama incoming.
    Intel    — integrated? brave.
    IDK      — we'll figure it out  (runs lspci | grep -i vga)
```

#### Screen 10 — Services and daemons
```
  WHAT SERVICES DO YOU WANT RUNNING?
  (sensible defaults already ticked)

  [x] NetworkManager      — you probably want internet
  [x] PipeWire            — audio. yes.
  [x] Bluetooth           — toggle if you don't need it
  [x] SSH daemon          — remote access
  [x] Docker              — only applies if you ticked Development
  [x] CUPS                — printing. uncheck if it's 2026 and you don't print
  [ ] Tailscale           — VPN mesh. opt-in.
  [ ] Syncthing           — file sync. opt-in.
  [ ] fail2ban            — brute force protection. recommended if SSH is on.
```

#### Screen 11 — NixOS channel
```
  PICK THE CHANNEL.
  IT'S KOREAN BARBECUE. YOU COOK IT YOURSELF.

  ❄️  Unstable (Zokor)   — bleeding edge. things occasionally break.
                           this is what kelvin was built on.
                           obviously the correct answer.

     Stable (Yarara)     — it works. boring. safe.
                           your mom would pick this.
```

#### Screen 12 — Kernel
```
  PICK YOUR KERNEL.
  boot.kernelPackages is a serious decision. choose wisely.

  ❄️  Zen            — recommended. optimized for desktop responsiveness.
                       lower latency, better interactivity. this is the move.

     LTS             — long term support. stable. boring. works.
                       good for servers or if zen ever breaks something.

     Latest          — bleeding edge kernel. newest features, newest bugs.
                       for people who like living dangerously.

     Hardened        — security-focused. some things will break.
                       if you need to ask, you don't need this.

     LQX             — liquorix. zen-based, more aggressive tweaks.
                       basically zen but louder.

     6.12 (older)    — pinned older version. for hardware that needs it.
     5.15 (older)    — LTS classic. if your machine hates the modern world.
     
  pick an older kernel and we won't stop you. we'll just judge you quietly.
```

#### Screen 13 — KDE Customization
```
  okay we're almost done. let's make it look like yours.

  ICON PACK:
    Papirus Dark   ← recommended
    Papirus Light
    Breeze
    Oxygen
    Tela

  SYSTEM FONT:
    Google Sans    ← recommended
    CaskaydiaCove  (monospace everywhere, terminal energy)
    IBM Plex Sans
    Noto Sans
    Keep default

  PLASMA COLOR SCHEME:
    Orchis Dark    ← recommended (modern, dark, clean)
    Breeze Dark
    Breeze Light
    Nordic
    Keep default
```

#### Screen 14 — Summary and confirm
```
  HERE'S WHAT YOU BUILT.

  Machine:      john-thinkpad  (x86_64)
  User:         john / john@example.com
  Disk:         /dev/nvme0n1 — WIPED
  Filesystem:   BTRFS + subvolumes + zstd compression
  Swap:         zram only
  Bootloader:   Limine (dark theme)
  Channel:      unstable (zokor)
  CPU:          Intel (microcode enabled)
  GPU:          AMD (amdgpu, vulkan)
  Services:     NetworkManager, PipeWire, Bluetooth, SSH, Docker, CUPS, fail2ban
  Packages:     Development, Gaming
  Icons:        Papirus
  Font:         Inter
  Theme:        Kelvin Dark

  if something's wrong, go back. if it's right:

  [ install kelvin. ]          [ X — go back ]
```

#### Installing (advanced)
```
        ❄️  K E L V I N  ❄️

  alright. generating your config.
  this is the part where you wait.

  ◐  partitioning /dev/nvme0n1...
  ✓  generating hardware configuration...
  ◐  building nix closures (this takes a while, get a coffee)...

  [████░░░░░░░░░░░░░░░░] 22%
```

---

## 4. Config Structure

Everything lives in `~/.kelvin/`. This is your entire system, readable and editable by you.

```
~/.kelvin/
├── flake.nix                    # root — defines everything, locked to zokor
├── flake.lock                   # pinned nixpkgs commit — reproducible installs
├── options.nix                  # THE file — all kelvin user choices live here
├── system/
│   ├── boot.nix                 # bootloader, kernel, zen tweaks
│   ├── networking.nix           # networkmanager, hostname, firewall
│   ├── locale.nix               # timezone, keyboard, language
│   ├── performance.nix          # zram, ananicy, vm params, zstd
│   └── services.nix             # ssh, cups, docker, bluetooth, etc.
├── hardware/
│   ├── generated.nix            # nixos-generate-config output — don't edit
│   ├── gpu.nix                  # amd/nvidia/intel specific config
│   └── cpu.nix                  # microcode, architecture-specific tweaks
├── desktop/
│   ├── kde.nix                  # plasma, sddm, wayland
│   ├── fonts.nix                # system fonts
│   └── theme.nix                # icons, color scheme, cursor
├── packages.nix                 # your installed packages — kelvin-store writes here
└── home/
    ├── default.nix              # home-manager root
    ├── zsh.nix                  # full zsh config, aliases, oh-my-zsh/starship
    └── git.nix                  # git user config from installer answers
```

### options.nix schema

```nix
# ~/.kelvin/options.nix
# Generated by the Kelvin installer. Edit freely.
{
  kelvin = {
    # Identity
    hostname     = "my-machine";
    username     = "john";
    fullName     = "John Doe";
    email        = "john@example.com";
    timezone     = "Europe/Bratislava";
    locale       = "en_US.UTF-8";
    keyboardLayout = "us";

    # Hardware
    gpu          = "amd";     # amd | nvidia | intel | auto
    cpu          = "intel";   # amd | intel | auto
    arch         = "x86_64";  # x86_64 | aarch64

    # Bootloader
    bootloader = {
      type        = "limine";  # limine | systemd-boot | grub
      theme       = "dark";    # light | dark
      generations = 2;         # how many generations to keep
    };

    # Filesystem
    filesystem   = "btrfs";   # btrfs | ext4 | xfs
    zstdCompression = true;
    swap         = "zram";    # zram | zram+swapfile | swapfile | none
    swapSize     = 0;         # GB, only used if swap includes swapfile

    # Channel
    channel      = "unstable"; # unstable | stable

    # Kernel
    kernel       = "zen";  # zen | lts | latest | hardened | lqx | 6_12 | 5_15

    # Use cases (from installer checkboxes)
    useCases = {
      development = true;
      gaming      = false;
      office      = false;
      media       = true;
      creative    = false;
    };

    # Desktop
    desktop = {
      iconPack    = "papirus-dark";  # papirus-dark | papirus-light | breeze | oxygen | tela
      font        = "google-sans";   # google-sans | caskaydia | ibm-plex | noto
      colorScheme = "orchis-dark";   # orchis-dark | breeze-dark | breeze-light | nordic
    };

    # Services
    services = {
      ssh         = true;
      cups        = true;
      bluetooth   = true;
      docker      = true;
      tailscale   = false;
      syncthing   = false;
      fail2ban    = true;
      ananicy     = true;
    };
  };
}
```

Every module reads from `cfg.kelvin.*`. The installer only ever writes this one file. Changing something post-install means editing `options.nix` and running `kelvin update` or `sudo nixos-rebuild switch`.

---

## 5. Bootloader

### Limine (default / recommended)
- `boot.loader.limine.enable = true`
- `boot.loader.limine.maxGenerations = cfg.kelvin.bootloader.generations` (default: 2)
- Generation labels: "Current Generation" and "Older Generation" (or "Older Generation 2" etc.)
- Two shipped wallpapers: `kelvin-boot-light.png` and `kelvin-boot-dark.png`
- Both feature the Kelvin snowflake logo centered on their respective backgrounds
- Branding color: Kelvin Blue (index 6 / cyan) for light theme, white for dark theme
- `boot.loader.limine.biosSupport = true` — works on BIOS and UEFI

### systemd-boot (alternative)
- No Kelvin theming applied
- UEFI only — installer warns if BIOS detected
- Generations still limited via `boot.loader.systemd-boot.configurationLimit`

### GRUB (legacy)
- Full BIOS and UEFI support
- Basic Kelvin branding applied via GRUB theme (best effort)
- Recommended only for old hardware

---

## 6. Package Categories

### Always installed (base)
Floorp, Konsole, Neovim, ZSH + config, btop, eza, fzf, pipewire, bluetooth utils, git, curl, wget, unzip, vlc, ffmpeg, yt-dlp, kelvin, kelvin-store, CaskaydiaCove Nerd Font, Google Sans font, CUPS

> **Note on Apple Silicon:** NixOS on M1/M2 Macs requires running the Asahi Linux installer first to set up the UEFI environment — the standard NixOS ISO flow is incompatible with Apple Silicon's boot architecture. Kelvin cannot support Apple Silicon in v1 for this reason. aarch64 generic (Raspberry Pi, ARM servers) may work but is untested.

### Development
VSCode, Claude Code, Antigravity CLI, Ollama, Docker + Docker Compose, Python 3 (numpy, pandas, matplotlib, scipy, requests, rich, httpx, jupyter, black, ruff, ipython), Node.js + npm, Neovim (already base), git (already base)

### Gaming
Steam, Lutris, Gamemode, Proton-GE, MangoHud, Gamescope, Wine, Winetricks

### Gaming Tweaks (Advanced only)
CPU governor switching tools, low-latency audio config (pipewire tuning), `gamemode` system-level tweaks, `schedulerctl` for real-time priority, optionally `cachyos-kernel` if available on nixpkgs

### Office
LibreOffice, Thunderbird, Obsidian, Okular

### Media
OBS, Spotify, Kdenlive, Handbrake (vlc and ffmpeg already base)

### Creative
GIMP, Inkscape, Krita, Kdenlive (if not already from Media)

### Science & Data
Jupyter, R + RStudio, Julia, TeXLive (full), gnuplot, SageMath, Zotero

### Privacy
Mullvad VPN, Tor Browser, Signal, ProtonMail Bridge, KeePassXC (always a good idea honestly)

### Server & Hosting
Portainer, nginx, Caddy, PostgreSQL, Redis, MariaDB

### Legacy Hardware Support (Advanced only)
`linux-firmware` extended blobs, Broadcom WiFi drivers, DKMS module support, older GPU mesa/driver overrides

### Virtualization (Advanced only)
virt-manager, QEMU, KVM, libvirt, Looking Glass client

### Security (Advanced only)
nmap, Wireshark, BurpSuite Community, Metasploit — advanced mode only, with a warning that these are serious tools

---

## 7. Kelvin Utilities

### `kelvin` — System Manager
A Rich-powered Python TUI. The flagship Kelvin tool.

**CLI usage:**
```
kelvin              # opens full TUI dashboard
kelvin update       # pull new nixpkgs, rebuild
kelvin rollback     # list generations, pick one, switch
kelvin status       # current gen, last update, nix store disk usage
kelvin clean        # garbage collect old generations (with confirmation)
kelvin doctor       # checks for common config issues
```

**TUI dashboard shows:**
- Current generation info and timestamp
- Last update date
- Nix store size
- Quick action buttons for update / rollback / clean

**KDE integration:**
- `.desktop` file: `Kelvin System Manager`
- Icon: Kelvin snowflake SVG
- Category: System
- Launches in Konsole

### `kelvin-store` — Package Manager
A Rich-powered Python TUI for searching and installing packages.

**Behavior:**
- Fuzzy search nixpkgs live via `nix search nixpkgs`
- Shows package name, version, description
- Tick to add, tick installed packages to remove
- Writes changes directly to `~/.kelvin/packages.nix`
- Prompts: "rebuild now or later?"
- If now: runs `sudo nixos-rebuild switch` with progress shown

**KDE integration:**
- `.desktop` file: `Kelvin Store`
- Icon: Kelvin snowflake SVG (or distinct variant)
- Category: System
- Launches in Konsole

---

## 8. KDE Plasma Configuration

Kelvin ships with KDE Plasma pre-configured. Out of the box:

- **Display server:** Wayland (X11 fallback available)
- **Login manager:** SDDM with Kelvin theme
- **Default browser:** Floorp
- **Default terminal:** Konsole
- **Default editor:** VSCode (if Development ticked), Kate otherwise
- **Taskbar:** bottom panel, centered icons (modern layout)
- **Virtual desktops:** 2 by default
- **Shortcuts:** standard KDE defaults preserved

### Configurable at install (Advanced mode):
- Icon pack (Papirus recommended)
- System font (Inter recommended)  
- Color scheme (Kelvin Dark recommended)

### Plasma Manager
KDE configuration is declared via `plasma-manager` nix module, meaning your entire KDE state is reproducible. Panel layout, shortcuts, default apps — all in `desktop/kde.nix`.

---

## 9. Development Phases

### Phase 1 — Identity and Design ← YOU ARE HERE
- [ ] Finalize this design document
- [ ] Design Kelvin snowflake SVG icon
- [ ] Finalize color palette hex values
- [ ] Write out both installer voice profiles completely
- [ ] Create GitHub repository

### Phase 2 — Installer
- [ ] Scaffold bash + gum installer script
- [ ] Simple mode — all screens
- [ ] Advanced mode — all screens
- [ ] Hardware autodetection (GPU, CPU, disk recommendation)
- [ ] Config generation (writes `~/.kelvin/` structure from answers)
- [ ] nixos-install integration
- [ ] VM testing on nixmac

### Phase 3 — Nix Config
- [ ] `flake.nix` skeleton with zokor input
- [ ] `options.nix` schema
- [ ] All modules reading from options
- [ ] Limine configured and themed
- [ ] Package categories declared
- [ ] Home-manager integration
- [ ] Bare metal test install

### Phase 4 — Kelvin Utilities
- [ ] `kelvin` Rich TUI system manager
- [ ] `kelvin-store` package search TUI
- [ ] `.desktop` files for both
- [ ] Packaged as nix derivations (installable from the flake)

### Phase 5 — Polish
- [ ] Full install test on ThinkPad T460s
- [ ] ISO build working (`nix build .#iso`)
- [ ] README with screenshots
- [ ] Boot splash / SDDM theme assets
- [ ] Portfolio write-up

---

## 10. Repository Structure

```
kelvin/
├── README.md
├── DESIGN.md              # this document
├── flake.nix              # ISO build + system config entry
├── iso.nix                # nixos-generators ISO definition
├── installer/
│   ├── install.sh         # main gum-based installer script
│   ├── simple.sh          # simple mode screens
│   ├── advanced.sh        # advanced mode screens
│   ├── detect.sh          # hardware autodetection utils
│   └── generate.sh        # config file generation from answers
├── modules/               # nixos modules
│   ├── system/
│   ├── hardware/
│   ├── desktop/
│   └── packages/
├── home/                  # home-manager modules
├── assets/
│   ├── kelvin.svg         # the snowflake icon
│   ├── boot-light.png     # limine light theme wallpaper
│   └── boot-dark.png      # limine dark theme wallpaper
└── tools/
    ├── kelvin/            # kelvin system manager (python/rich)
    └── kelvin-store/      # kelvin store (python/rich)
```

---

*Kelvin — built on NixOS 26.11 "Zokor". Every BYTE registered.*
