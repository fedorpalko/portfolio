#!/usr/bin/env bash
# Kelvin Advanced Mode Installer
# Voice profile: chaotic, roast-heavy, assumes competence.
# ALL CAPS for dramatic questions. Lowercase sarcasm for contrast.
# Still actually helpful — the aggression signals "pay attention, this matters."

KELVIN_DARK="${KELVIN_DARK:-#2A2A2A}"
KELVIN_WHITE="${KELVIN_WHITE:-#F5F5F5}"
KELVIN_ICE="${KELVIN_ICE:-#5BA4CF}"
KELVIN_BLUE="${KELVIN_BLUE:-#A8D8EA}"

# Collected answers
A_FULL_NAME=""
A_EMAIL=""
A_USERNAME=""
A_PASSWORD=""
A_HOSTNAME=""
A_TIMEZONE=""
A_KEYBOARD="us"
A_ARCH="x86_64"
A_ANANICY="yes"
A_USECASES=""
A_BOOTLOADER="limine"
A_BOOT_THEME="dark"
A_FILESYSTEM="btrfs"
A_COMPRESSION="yes"
A_SWAP="zram"
A_SWAP_SIZE="0"
A_DISK=""
A_PARTITION_SCHEME="auto"
A_CPU="auto"
A_GPU="auto"
A_CHANNEL="unstable"
A_KERNEL="zen"
A_ICON_PACK="Papirus-Dark"
A_FONT="inter"
A_COLOR_SCHEME="orchis-dark"
A_DISPLAY_MANAGER="ly"
A_SERVICES="NetworkManager PipeWire Bluetooth SSH"

# ─────────────────────────────────────────────────────────────────────────────

_adv_header() {
  gum style \
    --foreground "$KELVIN_WHITE" \
    --background "$KELVIN_DARK" \
    --border rounded \
    --border-foreground "$KELVIN_ICE" \
    --padding "1 4" \
    --margin "1 0 0 0" \
    --align center \
    --bold \
    --width 60 \
    "❄️  K E L V I N  ❄️"
  echo
}

_adv_box() {
  gum style \
    --foreground "$KELVIN_WHITE" \
    --background "$KELVIN_DARK" \
    --border rounded \
    --border-foreground "$KELVIN_ICE" \
    --padding "1 3" \
    --width 60 \
    "$@"
}

_adv_question() {
  gum style \
    --foreground "$KELVIN_ICE" \
    --bold \
    --padding "0 2" \
    "$@"
  echo
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 1 — Welcome
# ─────────────────────────────────────────────────────────────────────────────

advanced_screen_welcome() {
  clear
  _adv_header

  _adv_box \
    "What's up, I'm Kelvin, install me bitch." \
    "I want to know everything you put into me." \
    "Every BYTE will be registered." \
    "You're on your own lol."

  echo

  local choice
  choice=$(gum choose \
    --header "Well?" \
    --header.foreground "$KELVIN_ICE" \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "I'm ready." \
    "actually take me back to simple")

  if [[ "$choice" == "actually take me back to simple" ]]; then
    source "${SCRIPT_DIR}/simple.sh"
    run_simple_install
    exit 0
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 2 — Architecture check
# ─────────────────────────────────────────────────────────────────────────────

advanced_screen_arch() {
  clear
  _adv_header
  _adv_question "ARE WE x86_64?"

  A_ARCH=$(gum choose \
    --header.foreground "$KELVIN_ICE" \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "x86_64   — yes, normal computer, we can proceed" \
    "aarch64  — ARM. raspberry pi? some ARM server? you know what you're doing." \
    "Other    — godspeed")

  A_ARCH=$(echo "$A_ARCH" | awk '{print $1}')

  echo
  _adv_question "also, IS ANANICY-CPP APPLICABLE FOR YOUR USE CASE?"

  gum style --foreground "$KELVIN_WHITE" --padding "0 2" \
    "(process priority daemon, great for desktop responsiveness," \
    " irrelevant if this is a server)"
  echo

  local ananicy_choice
  ananicy_choice=$(gum choose \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "Yes, I use this as a desktop" \
    "No, skip it" \
    "What's ananicy-cpp?  ← okay maybe simple mode was right for you")

  case "$ananicy_choice" in
    "Yes"*)                     A_ANANICY="yes" ;;
    "No"*)                      A_ANANICY="no" ;;
    "What's"*)
      gum style --foreground "$KELVIN_ICE" --padding "0 2" \
        "ananicy-cpp is a daemon that adjusts process priorities" \
        "automatically. it makes your desktop snappier. just say yes."
      sleep 2
      A_ANANICY="yes"
      ;;
  esac
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 3 — Use cases
# ─────────────────────────────────────────────────────────────────────────────

advanced_screen_usecases() {
  clear
  _adv_header
  _adv_question "WHAT ARE WE BUILDING HERE."

  A_USECASES=$(gum choose \
    --no-limit \
    --header "spacebar = select, enter = confirm. pick what applies. we'll roast you if your picks contradict each other." \
    --header.foreground "$KELVIN_ICE" \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "Development      (vscode, docker, claude code, python, node, neovim)" \
    "Gaming           (steam, lutris, gamemode, proton, mangohud, gamescope)" \
    "Gaming Tweaks    (cpu governor, low-latency audio, cachyos-style tweaks)" \
    "Office           (libreoffice, thunderbird, obsidian)" \
    "Media            (vlc, ffmpeg, yt-dlp, obs, spotify)" \
    "Creative         (kdenlive, gimp, inkscape, krita)" \
    "Science & Data   (jupyter, pandas, R, julia, texlive, gnuplot)" \
    "Privacy          (mullvad, tor browser, signal, protonmail bridge)" \
    "Server           (portainer, nginx, caddy, postgresql, redis)" \
    "Legacy Hardware  (firmware blobs, broadcom wifi, older GPU support, DKMS)" \
    "Virtualization   (virt-manager, QEMU, KVM, looking glass)" \
    "Security         (nmap, wireshark, burpsuite, metasploit — you know what you're doing)")

  # Roast conflicting combos
  if echo "$A_USECASES" | grep -q "Gaming" && echo "$A_USECASES" | grep -q "Server"; then
    echo
    gum style --foreground "#FF9966" --padding "0 2" \
      "gaming AND server? i mean... respect the chaos i guess." \
      "just know gamemode will fight your postgresql for CPU priority."
    sleep 2
  fi

  if echo "$A_USECASES" | grep -q "Security" && echo "$A_USECASES" | grep -q "Privacy"; then
    echo
    gum style --foreground "#FF9966" --padding "0 2" \
      "security + privacy. you're either a researcher or extremely paranoid." \
      "either way, valid."
    sleep 1
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 4 — Identity
# ─────────────────────────────────────────────────────────────────────────────

advanced_screen_identity() {
  clear
  _adv_header
  _adv_question "who are you. git needs to know."

  A_FULL_NAME=$(gum input \
    --placeholder "your name" \
    --prompt "  name:      " \
    --prompt.foreground "$KELVIN_ICE")

  A_EMAIL=$(gum input \
    --placeholder "you@example.com" \
    --prompt "  email:     " \
    --prompt.foreground "$KELVIN_ICE")

  A_USERNAME=$(gum input \
    --placeholder "username" \
    --prompt "  username:  " \
    --prompt.foreground "$KELVIN_ICE")

  A_PASSWORD=$(gum input \
    --password \
    --placeholder "password" \
    --prompt "  password:  " \
    --prompt.foreground "$KELVIN_ICE")

  A_HOSTNAME=$(gum input \
    --placeholder "${A_USERNAME}-machine" \
    --value "${A_USERNAME}-machine" \
    --prompt "  hostname:  " \
    --prompt.foreground "$KELVIN_ICE")

  A_TIMEZONE=$(timedatectl list-timezones 2>/dev/null | gum filter \
    --placeholder "timezone..." \
    --prompt "  timezone:  " \
    --prompt.foreground "$KELVIN_ICE")
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 5 — Keyboard layout
# ─────────────────────────────────────────────────────────────────────────────

advanced_screen_keyboard() {
  clear
  _adv_header
  _adv_question "KEYBOARD LAYOUT."

  gum style --foreground "$KELVIN_WHITE" --padding "0 2" \
    "what layout is your keyboard. be honest."
  echo

  local choice
  choice=$(gum choose \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "us   — English (US)     ← probably this" \
    "gb   — English (UK)" \
    "de   — German" \
    "fr   — French" \
    "es   — Spanish" \
    "it   — Italian" \
    "pt   — Portuguese" \
    "ru   — Russian" \
    "sk   — Slovak" \
    "cz   — Czech" \
    "pl   — Polish" \
    "nl   — Dutch" \
    "Something else... — I need to search for it")

  if [[ "$choice" == "Something else..."* ]]; then
    gum style --foreground "$KELVIN_WHITE" --padding "0 2" \
      "fine. type to search xkb layouts. it won't hold your hand."
    echo
    A_KEYBOARD=$(localectl list-x11-keymap-layouts 2>/dev/null \
      | gum filter \
          --placeholder "type a layout code (e.g. dvorak, colemak, latam)..." \
          --prompt "  layout: " \
          --prompt.foreground "$KELVIN_ICE" \
          --height 12)
  else
    A_KEYBOARD=$(echo "$choice" | awk '{print $1}')
  fi

  # Final safety net. NB: must be an `if`, not `[[ -z … ]] && …` — under
  # `set -e` a trailing short-circuit that evaluates false makes the function
  # return non-zero, which aborts the whole installer the moment you pick a
  # (non-empty) layout.
  if [[ -z "$A_KEYBOARD" ]]; then A_KEYBOARD="us"; fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 6 — Bootloader
# ─────────────────────────────────────────────────────────────────────────────

advanced_screen_bootloader() {
  clear
  _adv_header
  _adv_question "PICK YOUR BOOTLOADER."

  local choice
  choice=$(gum choose \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "❄️  Limine        — recommended. modern, fast, pretty. kelvin themes apply here. supports BIOS and UEFI." \
    "   systemd-boot  — solid. boring. no themes. works everywhere. UEFI only." \
    "   GRUB          — legacy. slow. it'll boot anything. pick this if your machine is from 2009 or you love pain.")

  case "$choice" in
    *"Limine"*)       A_BOOTLOADER="limine" ;;
    *"systemd-boot"*) A_BOOTLOADER="systemd-boot" ;;
    *"GRUB"*)         A_BOOTLOADER="grub" ;;
  esac

  # Boot theme only if Limine
  if [[ "$A_BOOTLOADER" == "limine" ]]; then
    advanced_screen_boot_theme
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 6 — Boot theme (Limine only)
# ─────────────────────────────────────────────────────────────────────────────

advanced_screen_boot_theme() {
  clear
  _adv_header
  _adv_question "BOOTLOADER THEME."

  gum style --foreground "$KELVIN_WHITE" --padding "0 2" \
    "(you picked limine, good. now make it yours.)"
  echo

  local choice
  choice=$(gum choose \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "❄️ Light  — kelvin blue and white. clean. friendly. the correct choice." \
    "   Dark   — dark grey and white. serious. for people who think light mode is for children.")

  case "$choice" in
    *"Light"*) A_BOOT_THEME="light" ;;
    *"Dark"*)  A_BOOT_THEME="dark" ;;
  esac
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 7 — Filesystem
# ─────────────────────────────────────────────────────────────────────────────

advanced_screen_filesystem() {
  clear
  _adv_header
  _adv_question "DO YOU WANT BTRFS SUBVOLUMES?"

  gum style --foreground "$KELVIN_WHITE" --padding "0 2" \
    "if you don't know what that means, hit X and go back to simple." \
    "if you do — yes means snapshots, rollbacks, compression." \
    "obviously the correct answer is yes."
  echo

  local fs_choice
  fs_choice=$(gum choose \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "BTRFS with subvolumes   ← DO THIS" \
    "ext4                    — okay. coward. but okay." \
    "XFS                     — interesting choice. respected.")

  case "$fs_choice" in
    "BTRFS"*) A_FILESYSTEM="btrfs" ;;
    "ext4"*)  A_FILESYSTEM="ext4" ;;
    "XFS"*)   A_FILESYSTEM="xfs" ;;
  esac

  echo
  _adv_question "SWAP CONFIGURATION:"

  local swap_choice
  swap_choice=$(gum choose \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "zram only (recommended)  — fast, RAM-based, no swap partition" \
    "zram + swapfile          — belt and suspenders" \
    "swapfile only            — why" \
    "none                     — you're on your own if you OOM")

  case "$swap_choice" in
    "zram only"*)    A_SWAP="zram" ;;
    "zram + swap"*)  A_SWAP="zram+swapfile"
      A_SWAP_SIZE=$(gum input --placeholder "4" --prompt "  Swapfile size (GB): " --prompt.foreground "$KELVIN_ICE")
      ;;
    "swapfile only"*) A_SWAP="swapfile"
      A_SWAP_SIZE=$(gum input --placeholder "4" --prompt "  Swapfile size (GB): " --prompt.foreground "$KELVIN_ICE")
      ;;
    "none"*)         A_SWAP="none" ;;
  esac

  # ZSTD compression (BTRFS only)
  if [[ "$A_FILESYSTEM" == "btrfs" ]]; then
    echo
    _adv_question "ZSTD COMPRESSION?"

    local zstd_choice
    zstd_choice=$(gum choose \
      --item.foreground "$KELVIN_WHITE" \
      --selected.foreground "$KELVIN_WHITE" \
      --selected.background "$KELVIN_ICE" \
      "Yes  — smaller disk usage, negligible CPU overhead. yes." \
      "No   — leaving performance on the table, but it's your life.")

    case "$zstd_choice" in
      "Yes"*) A_COMPRESSION="yes" ;;
      "No"*)  A_COMPRESSION="no" ;;
    esac
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 8 — Disk
# ─────────────────────────────────────────────────────────────────────────────

advanced_screen_disk() {
  clear
  _adv_header
  _adv_question "PICK THE DISK. THIS WIPES IT."

  local disk_options
  disk_options=$(detect_disks_advanced)

  A_DISK=$(echo "$disk_options" | gum choose \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE")

  A_DISK=$(echo "$A_DISK" | awk '{print $1}')

  echo
  _adv_question "PARTITION SCHEME:"

  local part_choice
  part_choice=$(gum choose \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "Auto (recommended)  — EFI 512MB, root takes the rest" \
    "Manual              — you specify sizes. you know the risks.")

  case "$part_choice" in
    "Auto"*)   A_PARTITION_SCHEME="auto" ;;
    "Manual"*) A_PARTITION_SCHEME="manual"
      # TODO: implement interactive manual partitioning
      gum style --foreground "#FF9966" --padding "0 2" \
        "manual partitioning not yet implemented in this version." \
        "falling back to auto. sorry."
      A_PARTITION_SCHEME="auto"
      ;;
  esac
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 9 — Hardware
# ─────────────────────────────────────────────────────────────────────────────

advanced_screen_hardware() {
  clear
  _adv_header
  _adv_question "CPU MANUFACTURER?"

  local cpu_choice
  cpu_choice=$(gum choose \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "AMD      — good taste" \
    "Intel    — respectable" \
    "IDK      — we'll figure it out")

  case "$cpu_choice" in
    "AMD"*)   A_CPU="amd" ;;
    "Intel"*) A_CPU="intel" ;;
    "IDK"*)
      A_CPU=$(detect_cpu)
      gum style --foreground "$KELVIN_ICE" --padding "0 2" "  detected: ${A_CPU}"
      sleep 1
      ;;
  esac

  echo
  _adv_question "GPU SITUATION?"

  local gpu_choice
  gpu_choice=$(gum choose \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "AMD      — excellent. open source drivers. the way." \
    "NVIDIA   — respect. we'll make it work. proprietary drama incoming." \
    "Intel    — integrated? brave." \
    "IDK      — we'll figure it out")

  case "$gpu_choice" in
    "AMD"*)    A_GPU="amd" ;;
    "NVIDIA"*)
      A_GPU="nvidia"
      gum style --foreground "#FF9966" --padding "0 2" \
        "NVIDIA detected. enabling proprietary drivers." \
        "if something breaks, it's nvidia's fault, not kelvin's."
      sleep 1
      ;;
    "Intel"*)  A_GPU="intel" ;;
    "IDK"*)
      A_GPU=$(detect_gpu)
      gum style --foreground "$KELVIN_ICE" --padding "0 2" "  detected: ${A_GPU}"
      sleep 1
      ;;
  esac
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 10 — Services
# ─────────────────────────────────────────────────────────────────────────────

advanced_screen_services() {
  clear
  _adv_header
  _adv_question "WHAT SERVICES DO YOU WANT RUNNING?"

  gum style --foreground "$KELVIN_WHITE" --padding "0 2" "(sensible defaults already ticked)"
  echo

  A_SERVICES=$(gum choose \
    --no-limit \
    --selected "NetworkManager — you probably want internet" \
    --selected "PipeWire — audio. yes." \
    --selected "Bluetooth — toggle if you don't need it" \
    --selected "SSH daemon — remote access" \
    --selected "CUPS — printing" \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "NetworkManager — you probably want internet" \
    "PipeWire — audio. yes." \
    "Bluetooth — toggle if you don't need it" \
    "SSH daemon — remote access" \
    "Docker — only applies if you ticked Development" \
    "CUPS — printing. uncheck if it's 2026 and you don't print" \
    "Tailscale — VPN mesh. opt-in." \
    "Syncthing — file sync. opt-in." \
    "fail2ban — brute force protection. recommended if SSH is on.")
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 11 — Channel
# ─────────────────────────────────────────────────────────────────────────────

advanced_screen_channel() {
  clear
  _adv_header
  _adv_question "PICK THE CHANNEL."

  gum style --foreground "$KELVIN_WHITE" --padding "0 2" \
    "IT'S KOREAN BARBECUE. YOU COOK IT YOURSELF."
  echo

  local choice
  choice=$(gum choose \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "❄️  Unstable (Zokor)  — bleeding edge. things occasionally break. this is what kelvin was built on. obviously the correct answer." \
    "   Stable (Yarara)   — it works. boring. safe. your mom would pick this.")

  case "$choice" in
    *"Unstable"*) A_CHANNEL="unstable" ;;
    *"Stable"*)   A_CHANNEL="stable" ;;
  esac
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 12 — Kernel
# ─────────────────────────────────────────────────────────────────────────────

advanced_screen_kernel() {
  clear
  _adv_header
  _adv_question "PICK YOUR KERNEL."

  gum style --foreground "$KELVIN_WHITE" --padding "0 2" \
    "boot.kernelPackages is a serious decision. choose wisely."
  echo

  local choice
  choice=$(gum choose \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "❄️  Zen      — recommended. optimized for desktop. lower latency, better interactivity. this is the move." \
    "   LTS       — long term support. stable. boring. good for servers." \
    "   Latest    — bleeding edge. newest features, newest bugs. living dangerously." \
    "   Hardened  — security-focused. some things will break. if you need to ask, you don't need this." \
    "   LQX       — liquorix. zen-based, more aggressive tweaks. basically zen but louder." \
    "   6.12      — pinned older version. for hardware that needs it." \
    "   5.15      — LTS classic. if your machine hates the modern world.")

  case "$choice" in
    *"Zen"*)      A_KERNEL="zen" ;;
    *"LTS"*)      A_KERNEL="lts" ;;
    *"Latest"*)   A_KERNEL="latest" ;;
    *"Hardened"*) A_KERNEL="hardened" ;;
    *"LQX"*)      A_KERNEL="lqx" ;;
    *"6.12"*)     A_KERNEL="6_12"
      gum style --foreground "#FF9966" --padding "0 2" "we won't stop you. we'll just judge you quietly."
      sleep 1 ;;
    *"5.15"*)     A_KERNEL="5_15"
      gum style --foreground "#FF9966" --padding "0 2" "we won't stop you. we'll just judge you quietly."
      sleep 1 ;;
  esac
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 13 — KDE customization
# ─────────────────────────────────────────────────────────────────────────────

advanced_screen_kde() {
  clear
  _adv_header

  gum style --foreground "$KELVIN_WHITE" --padding "0 2" \
    "okay we're almost done. let's make it look like yours."
  echo

  _adv_question "ICON PACK:"
  A_ICON_PACK=$(gum choose \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "Papirus Dark   ← recommended" \
    "Papirus Light" \
    "Breeze" \
    "Oxygen" \
    "Tela")

  case "$A_ICON_PACK" in
    "Papirus Dark"*)  A_ICON_PACK="papirus-dark" ;;
    "Papirus Light"*) A_ICON_PACK="papirus-light" ;;
    "Breeze"*)        A_ICON_PACK="breeze" ;;
    "Oxygen"*)        A_ICON_PACK="oxygen" ;;
    "Tela"*)          A_ICON_PACK="tela" ;;
  esac

  echo
  _adv_question "SYSTEM FONT:"
  A_FONT=$(gum choose \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "Inter          ← recommended" \
    "IBM Plex Sans" \
    "Noto Sans")

  case "$A_FONT" in
    "Inter"*)     A_FONT="inter" ;;
    "IBM Plex"*)  A_FONT="ibm-plex" ;;
    "Noto"*)      A_FONT="noto" ;;
    *)            A_FONT="inter" ;;
  esac

  echo
  _adv_question "GLOBAL THEME / COLOR SCHEME:"
  A_COLOR_SCHEME=$(gum choose \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "Orchis Dark    ← recommended (modern, dark, clean)" \
    "Orchis Light   (same Orchis look, bright)" \
    "Breeze Dark" \
    "Breeze Light" \
    "Nordic" \
    "Keep default")

  case "$A_COLOR_SCHEME" in
    "Orchis Dark"*)  A_COLOR_SCHEME="orchis-dark" ;;
    "Orchis Light"*) A_COLOR_SCHEME="orchis-light" ;;
    "Breeze Dark"*)  A_COLOR_SCHEME="breeze-dark" ;;
    "Breeze Light"*) A_COLOR_SCHEME="breeze-light" ;;
    "Nordic"*)       A_COLOR_SCHEME="nordic" ;;
    *)               A_COLOR_SCHEME="orchis-dark" ;;
  esac
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 13b — Display manager
# ─────────────────────────────────────────────────────────────────────────────

advanced_screen_displaymanager() {
  clear
  _adv_header
  _adv_question "DISPLAY MANAGER."

  gum style --foreground "$KELVIN_WHITE" --padding "0 2" \
    "who greets you at the door. ly is default — minimal and fast."
  echo

  local choice
  choice=$(gum choose \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "ly       — minimal TUI greeter  ← recommended (default)" \
    "SDDM     — graphical, Kelvin-themed (native to Plasma)" \
    "GDM      — GNOME's, great Wayland support (heavier)" \
    "greetd   — modern minimal login + tuigreet TUI" \
    "LightDM  — GTK greeter, Mint-style")

  case "$choice" in
    "ly"*)      A_DISPLAY_MANAGER="ly" ;;
    "SDDM"*)    A_DISPLAY_MANAGER="sddm" ;;
    "GDM"*)     A_DISPLAY_MANAGER="gdm" ;;
    "greetd"*)  A_DISPLAY_MANAGER="greetd" ;;
    "LightDM"*) A_DISPLAY_MANAGER="lightdm" ;;
    *)          A_DISPLAY_MANAGER="ly" ;;
  esac
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 14 — Summary + confirm
# ─────────────────────────────────────────────────────────────────────────────

advanced_screen_confirm() {
  clear
  _adv_header
  _adv_question "HERE'S WHAT YOU BUILT."

  gum style \
    --foreground "$KELVIN_WHITE" \
    --background "$KELVIN_DARK" \
    --border rounded \
    --border-foreground "$KELVIN_ICE" \
    --padding "1 3" \
    --width 60 \
    "Machine:      ${A_HOSTNAME}  (${A_ARCH})" \
    "User:         ${A_USERNAME} / ${A_EMAIL}" \
    "Disk:         ${A_DISK} — WIPED" \
    "Filesystem:   ${A_FILESYSTEM}${A_COMPRESSION:+ + zstd compression}" \
    "Swap:         ${A_SWAP}" \
    "Bootloader:   ${A_BOOTLOADER} (${A_BOOT_THEME} theme)" \
    "Channel:      ${A_CHANNEL}" \
    "Kernel:       ${A_KERNEL}" \
    "CPU:          ${A_CPU}" \
    "GPU:          ${A_GPU}" \
    "Icons:        ${A_ICON_PACK}" \
    "Font:         ${A_FONT}" \
    "Theme:        ${A_COLOR_SCHEME}" \
    "Login:        ${A_DISPLAY_MANAGER}"

  echo
  gum style --foreground "$KELVIN_WHITE" --padding "0 2" \
    "if something's wrong, go back. if it's right:"
  echo

  gum confirm \
    --prompt.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "" \
    --affirmative "install kelvin." \
    --negative "X — go back" || return 1

  return 0
}

# ─────────────────────────────────────────────────────────────────────────────
# Installing (advanced)
# ─────────────────────────────────────────────────────────────────────────────

# Shown when any install step fails. Names the failed step, then exits the
# installer non-zero. On the ISO the installer runs as a child of the tty1 login
# shell (see iso.nix), so exiting drops the user to an interactive root prompt
# with this error still on screen — no auto-relaunch loop. The target system is
# left mounted at /mnt for investigation.
_advanced_install_failed() {
  local step="$1"
  clear

  gum style \
    --foreground "$KELVIN_WHITE" \
    --background "#FF6B6B" \
    --border rounded \
    --border-foreground "#FF6B6B" \
    --padding "1 3" \
    --width 60 \
    "installation failed." \
    "" \
    "step that failed:" \
    "  ${step}"

  echo
  # Show the captured output of the failed step. The screen was cleared above,
  # so gum spin's own output is gone — this is the only place the real error
  # (e.g. from disko / nixos-install) is visible.
  if [[ -s /tmp/kelvin-install.log ]]; then
    gum style --foreground "#FF6B6B" "  ─── error output (last 40 lines) ───"
    echo
    tail -n 40 /tmp/kelvin-install.log
    echo
  fi

  gum style --foreground "$KELVIN_WHITE" \
    "the target system is mounted at /mnt if you want to investigate." \
    "full log: /tmp/kelvin-install.log" \
    "" \
    "press Enter to drop to a shell."

  echo
  # Pause so the error is readable even outside the ISO's login-shell safety net.
  read -r _ || true
  exit 1
}

# Run one install step with a spinner.
#
# `gum spin` executes its command as a *child process*, so it cannot call the
# shell functions defined in generate.sh (partition_disk_advanced,
# generate_kelvin_config_advanced) directly — they aren't on PATH. Previously
# this meant the very first step failed instantly and `set -e` killed the whole
# script, bouncing the user back to the start. We fix that by running every step
# inside a child bash that first sources generate.sh, so both shell-function
# steps and plain binaries (nixos-install, …) work uniformly. The A_* answers
# are exported (see advanced_screen_installing) so the child shell can read them.
#
# On failure we surface the captured output (gum spin --show-error) and drop to
# a shell, rather than letting `set -e` abort silently.
_advanced_step() {
  local title="$1"
  shift
  # Run the step under a spinner, teeing its combined stdout+stderr to a log.
  # gum spin hides command output and the failure screen clears the terminal, so
  # without this capture the real error (e.g. from disko) is never visible.
  # `exit ${PIPESTATUS[0]}` preserves the step's real exit code through the tee.
  if ! gum spin --spinner dot --title "$title" -- \
      bash -c 'source "$0"; "$@" 2>&1 | tee /tmp/kelvin-install.log; exit "${PIPESTATUS[0]}"' \
      "${SCRIPT_DIR}/generate.sh" "$@"; then
    _advanced_install_failed "$title"
  fi
}

advanced_screen_installing() {
  clear
  _adv_header

  gum style \
    --foreground "$KELVIN_WHITE" \
    --background "$KELVIN_DARK" \
    --padding "1 4" \
    --align center \
    --width 60 \
    "alright. generating your config." \
    "this is the part where you wait."

  echo

  # Export the collected answers so the child shells spawned by _advanced_step
  # (which source generate.sh) can read them.
  export A_FULL_NAME A_EMAIL A_USERNAME A_PASSWORD A_HOSTNAME A_TIMEZONE \
         A_KEYBOARD A_ARCH A_ANANICY A_USECASES A_BOOTLOADER A_BOOT_THEME \
         A_FILESYSTEM A_COMPRESSION A_SWAP A_SWAP_SIZE A_DISK A_PARTITION_SCHEME \
         A_CPU A_GPU A_CHANNEL A_KERNEL A_ICON_PACK A_FONT A_COLOR_SCHEME \
         A_DISPLAY_MANAGER A_SERVICES

  _advanced_step "partitioning ${A_DISK}..." \
    partition_disk_advanced "$A_DISK" "$A_FILESYSTEM" "$A_SWAP" "$A_SWAP_SIZE" "$A_COMPRESSION"

  # --no-filesystems: disko owns fileSystems/swapDevices (see disko.nix). Without
  # this flag nixos-generate-config emits its own UUID-keyed fileSystems."/",
  # which conflicts with disko's by-partlabel definition and fails the build with
  # "The option `fileSystems.\"/\".device' has conflicting definition values".
  _advanced_step "generating hardware configuration..." \
    nixos-generate-config --no-filesystems --root /mnt

  _advanced_step "writing kelvin configuration..." \
    generate_kelvin_config_advanced

  _advanced_step "building nix closures (this takes a while, get a coffee)..." \
    nixos-install --root /mnt --flake "/mnt/home/${A_USERNAME}/.kelvin/#kelvin" --no-root-passwd

  _advanced_step "setting password..." \
    bash -c "echo '${A_USERNAME}:${A_PASSWORD}' | nixos-enter --root /mnt -- chpasswd"

  return 0
}

# ─────────────────────────────────────────────────────────────────────────────
# Main flow
# ─────────────────────────────────────────────────────────────────────────────

run_advanced_install() {
  advanced_screen_welcome
  advanced_screen_arch
  advanced_screen_usecases
  advanced_screen_identity
  advanced_screen_keyboard
  advanced_screen_bootloader
  advanced_screen_filesystem
  advanced_screen_disk
  advanced_screen_hardware
  advanced_screen_services
  advanced_screen_channel
  advanced_screen_kernel
  advanced_screen_kde
  advanced_screen_displaymanager

  if advanced_screen_confirm; then
    # advanced_screen_installing handles its own failures (it drops to a shell),
    # so it only returns success once the whole install has completed. Guard the
    # done screen on that success so a failed install can never fall through to
    # "done. everything is registered."
    if advanced_screen_installing; then
      clear
      _adv_header
      gum style \
        --foreground "$KELVIN_WHITE" \
        --background "$KELVIN_DARK" \
        --border double \
        --border-foreground "$KELVIN_ICE" \
        --padding "2 4" \
        --align center \
        --width 60 \
        "❄️  K E L V I N  ❄️" \
        "" \
        "done. everything is registered." \
        "reboot and it's yours."

      echo
      gum confirm --affirmative "reboot." --negative "stay here" && reboot || true
    fi
  else
    run_advanced_install
  fi
}
