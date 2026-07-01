#!/usr/bin/env bash
# Kelvin Simple Mode Installer
# Voice profile: warm, encouraging, second-person friendly.
# Celebrates small wins. Never uses jargon without explaining it.

KELVIN_BLUE="${KELVIN_BLUE:-#A8D8EA}"
KELVIN_WHITE="${KELVIN_WHITE:-#F5F5F5}"
KELVIN_ICE="${KELVIN_ICE:-#5BA4CF}"
KELVIN_DARK="${KELVIN_DARK:-#2A2A2A}"

# Collected answers
S_FULL_NAME=""
S_EMAIL=""
S_USERNAME=""
S_PASSWORD=""
S_TIMEZONE=""
S_KEYBOARD="us"
S_DISK=""
S_DISK_MODEL=""
S_DISK_SIZE=""
S_USECASES=""
S_HOSTNAME=""

# ─────────────────────────────────────────────────────────────────────────────

_simple_header() {
  gum style \
    --foreground "$KELVIN_WHITE" \
    --background "$KELVIN_BLUE" \
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

_simple_box() {
  gum style \
    --foreground "$KELVIN_DARK" \
    --background "$KELVIN_BLUE" \
    --border rounded \
    --border-foreground "$KELVIN_ICE" \
    --padding "1 3" \
    --width 60 \
    "$@"
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 1 — Welcome
# ─────────────────────────────────────────────────────────────────────────────

simple_screen_welcome() {
  clear
  _simple_header

  _simple_box \
    "Hey, I'm Kelvin, your new computer operating" \
    "system, and I'm here to help you install me!" \
    "" \
    "This should only take a few minutes." \
    "Let's get started!"

  echo
  gum confirm \
    --prompt.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "Ready?" \
    --affirmative "Let's go!" \
    --negative "Wait, what is this?" || {
      _simple_box "Kelvin is a custom Linux operating system." \
        "It's based on NixOS, which means everything" \
        "is configured automatically and reproducibly." \
        "" \
        "You don't need to know any of that." \
        "Just answer the questions and I'll handle it."
      echo
      gum confirm --affirmative "Got it, let's go!" --negative "Exit" || exit 0
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 2 — What's this computer for?
# ─────────────────────────────────────────────────────────────────────────────

simple_screen_usecases() {
  clear
  _simple_header

  gum style \
    --foreground "$KELVIN_DARK" \
    --padding "0 2" \
    "First things first — what will you do on this computer?" \
    "Pick everything that applies. You can always add more later!"

  echo

  S_USECASES=$(gum choose \
    --no-limit \
    --header "Use the spacebar to select, Enter to confirm." \
    --header.foreground "$KELVIN_ICE" \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "Development      (code editors, docker, AI tools, Python, Node)" \
    "Gaming           (Steam, Lutris, Proton, game optimizations)" \
    "Office Work      (LibreOffice, email, notes, document stuff)" \
    "Media            (YouTube downloader, video editing, streaming, music)" \
    "Creative Work    (design tools, image editing, illustration)" \
    "Science & Data   (Jupyter, data tools, LaTeX, R)" \
    "Privacy          (VPN tools, encrypted messaging, Tor browser)" \
    "Server & Hosting (docker, portainer, nginx, self-hosting tools)")

  if [[ -z "$S_USECASES" ]]; then
    gum style --foreground "$KELVIN_ICE" "  (nothing selected — that's fine, you can add things later)"
    echo
    gum confirm --affirmative "Continue" --negative "Go back" || simple_screen_usecases
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 3 — About you
# ─────────────────────────────────────────────────────────────────────────────

simple_screen_identity() {
  clear
  _simple_header

  gum style \
    --foreground "$KELVIN_DARK" \
    --padding "0 2" \
    "Now, a little about you." \
    "This sets up your account and git configuration."

  echo

  S_FULL_NAME=$(gum input \
    --placeholder "John Doe" \
    --prompt "  What's your name?       " \
    --prompt.foreground "$KELVIN_ICE")

  S_EMAIL=$(gum input \
    --placeholder "john@example.com" \
    --prompt "  What's your email?      " \
    --prompt.foreground "$KELVIN_ICE")

  # Suggest a username from the full name
  local suggested_user
  suggested_user=$(echo "$S_FULL_NAME" | tr '[:upper:]' '[:lower:]' | awk '{print $1}' | tr -cd 'a-z0-9')

  S_USERNAME=$(gum input \
    --placeholder "${suggested_user:-john}" \
    --value "${suggested_user:-}" \
    --prompt "  Pick a username          " \
    --prompt.foreground "$KELVIN_ICE")

  # Default hostname from username
  S_HOSTNAME="${S_USERNAME}-pc"

  echo
  gum style --foreground "$KELVIN_ICE" --padding "0 2" "  Now pick a password. Make sure you can remember it!"
  echo

  local pass_confirm
  S_PASSWORD=$(gum input \
    --password \
    --placeholder "············" \
    --prompt "  Password                " \
    --prompt.foreground "$KELVIN_ICE")

  pass_confirm=$(gum input \
    --password \
    --placeholder "············" \
    --prompt "  Confirm password        " \
    --prompt.foreground "$KELVIN_ICE")

  if [[ "$S_PASSWORD" != "$pass_confirm" ]]; then
    gum style --foreground "#FF6B6B" "  Passwords don't match. Let's try that again."
    echo
    sleep 1
    simple_screen_identity
    return
  fi

  if [[ ${#S_PASSWORD} -lt 8 ]]; then
    gum style --foreground "#FF6B6B" "  That password is pretty short. At least 8 characters, please!"
    echo
    sleep 1
    simple_screen_identity
    return
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 4 — Where are you?
# ─────────────────────────────────────────────────────────────────────────────

simple_screen_locale() {
  clear
  _simple_header

  gum style \
    --foreground "$KELVIN_DARK" \
    --padding "0 2" \
    "Let's set your timezone so your clock is right." \
    "Start typing to search — there are a lot of options!"

  echo

  local tz_list
  tz_list=$(timedatectl list-timezones 2>/dev/null || find /usr/share/zoneinfo -type f | sed 's|/usr/share/zoneinfo/||' | sort)

  S_TIMEZONE=$(echo "$tz_list" | gum filter \
    --placeholder "Type to search timezones..." \
    --prompt "  Timezone: " \
    --prompt.foreground "$KELVIN_ICE" \
    --header "Search your timezone (e.g. Europe/London, America/New_York)" \
    --header.foreground "$KELVIN_WHITE")

  echo
  gum style --foreground "$KELVIN_DARK" --padding "0 2" "  Keyboard layout:"
  echo

  S_KEYBOARD=$(gum choose \
    --header "Pick your keyboard layout:" \
    --header.foreground "$KELVIN_ICE" \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "English (US)  ← recommended" \
    "English (UK)" \
    "Slovak" \
    "Czech" \
    "German" \
    "French" \
    "Spanish" \
    "Other (you'll need to set this manually later)")

  # Map selection to xkb layout code
  case "$S_KEYBOARD" in
    "English (US)"*) S_KEYBOARD="us" ;;
    "English (UK)"*) S_KEYBOARD="gb" ;;
    "Slovak"*)       S_KEYBOARD="sk" ;;
    "Czech"*)        S_KEYBOARD="cz" ;;
    "German"*)       S_KEYBOARD="de" ;;
    "French"*)       S_KEYBOARD="fr" ;;
    "Spanish"*)      S_KEYBOARD="es" ;;
    *)               S_KEYBOARD="us" ;;
  esac
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 5 — The disk
# ─────────────────────────────────────────────────────────────────────────────

simple_screen_disk() {
  clear
  _simple_header

  gum style \
    --foreground "$KELVIN_DARK" \
    --padding "0 2" \
    "Which disk should Kelvin go on?" \
    "We'll be wiping it completely — so choose carefully!"

  echo

  local disk_options
  disk_options=$(detect_disks_simple)

  if [[ -z "$disk_options" ]]; then
    gum style --foreground "#FF6B6B" "  No disks detected. Something is very wrong."
    exit 1
  fi

  S_DISK=$(echo "$disk_options" | gum choose \
    --header "Select the disk for installation:" \
    --header.foreground "$KELVIN_ICE" \
    --item.foreground "$KELVIN_WHITE" \
    --selected.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE")

  # Extract just the /dev/xxx path, then capture model and size for the summary
  S_DISK=$(echo "$S_DISK" | awk '{print $1}')
  S_DISK_MODEL=$(lsblk -d -n -o MODEL "$S_DISK" 2>/dev/null | sed 's/  */ /g;s/^ //;s/ $//')
  S_DISK_SIZE=$(lsblk -d -n -o SIZE  "$S_DISK" 2>/dev/null | tr -d ' ')

  echo
  gum style --foreground "$KELVIN_ICE" --padding "0 2" \
    "  (we highlighted the one that looks most like a system drive)" \
    "  (if you're not sure, the biggest non-USB drive is usually right)"
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 6 — Confirmation
# ─────────────────────────────────────────────────────────────────────────────

simple_screen_confirm() {
  clear
  _simple_header

  gum style \
    --foreground "$KELVIN_DARK" \
    --padding "0 2" \
    "Here's what we're going to do:"

  echo

  gum style \
    --foreground "$KELVIN_WHITE" \
    --background "$KELVIN_ICE" \
    --padding "1 3" \
    --width 60 \
    "✓  Install Kelvin on ${S_DISK} (${S_DISK_MODEL}, ${S_DISK_SIZE})" \
    "✓  Create account: ${S_USERNAME}" \
    "✓  Timezone: ${S_TIMEZONE}" \
    "✓  Keyboard: ${S_KEYBOARD}" \
    "✓  Packages: ${S_USECASES:-none selected}"

  echo
  gum style \
    --foreground "#FF9966" \
    --padding "0 2" \
    "  Did you pick the right disk? This will erase everything on ${S_DISK}."

  echo

  gum confirm \
    --prompt.foreground "$KELVIN_WHITE" \
    --selected.background "$KELVIN_ICE" \
    "Ready to install?" \
    --affirmative "Yes, let's go!" \
    --negative "Wait, go back" || return 1

  return 0
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 7 — Installing
# ─────────────────────────────────────────────────────────────────────────────

# Shown when any install step fails. Names the failed step, then exits the
# installer non-zero. On the ISO the installer runs as a child of the tty1 login
# shell (see iso.nix), so exiting drops the user to an interactive root prompt
# with this error still on screen — no auto-relaunch loop. The target system is
# left mounted at /mnt for investigation.
_simple_install_failed() {
  local step="$1"
  clear

  gum style \
    --foreground "$KELVIN_WHITE" \
    --background "#FF6B6B" \
    --border rounded \
    --border-foreground "#FF6B6B" \
    --padding "1 3" \
    --width 60 \
    "Something went wrong while installing." \
    "" \
    "Step that failed:" \
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
    "The target system is mounted at /mnt if you want to poke around." \
    "Full log: /tmp/kelvin-install.log" \
    "" \
    "Press Enter to drop to a shell."

  echo
  # Pause so the error is readable even outside the ISO's login-shell safety net.
  read -r _ || true
  exit 1
}

# Run one install step with a spinner.
#
# `gum spin` executes its command as a *child process*, so it cannot call the
# shell functions defined in generate.sh (partition_disk_simple,
# generate_kelvin_config_simple) directly — they aren't on PATH. Previously this
# meant the very first step failed instantly and `set -e` killed the whole
# script, bouncing the user back to the start. We fix that by running every step
# inside a child bash that first sources generate.sh, so both shell-function
# steps and plain binaries (nixos-install, …) work uniformly. The S_* answers
# are exported (see simple_screen_installing) so the child shell can read them.
#
# On failure we surface the captured output (gum spin --show-error) and drop to
# a shell, rather than letting `set -e` abort silently.
_simple_step() {
  local title="$1"
  shift
  # Run the step under a spinner, teeing its combined stdout+stderr to a log.
  # gum spin hides command output and the failure screen clears the terminal, so
  # without this capture the real error (e.g. from disko) is never visible.
  # `exit ${PIPESTATUS[0]}` preserves the step's real exit code through the tee.
  if ! gum spin --spinner dot --title "$title" -- \
      bash -c 'source "$0"; "$@" 2>&1 | tee /tmp/kelvin-install.log; exit "${PIPESTATUS[0]}"' \
      "${SCRIPT_DIR}/generate.sh" "$@"; then
    _simple_install_failed "$title"
  fi
}

simple_screen_installing() {
  clear
  _simple_header

  gum style \
    --foreground "$KELVIN_WHITE" \
    --background "$KELVIN_BLUE" \
    --padding "1 4" \
    --align center \
    --width 60 \
    "hey, great job. now sit back, grab a drink —" \
    "Kelvin is installing. we'll let you know when" \
    "it's done."

  echo

  # Export the collected answers so the child shells spawned by _simple_step
  # (which source generate.sh) can read them.
  export S_FULL_NAME S_EMAIL S_USERNAME S_PASSWORD S_TIMEZONE \
         S_KEYBOARD S_DISK S_USECASES S_HOSTNAME

  _simple_step "Partitioning ${S_DISK}..." \
    partition_disk_simple "$S_DISK"

  # --no-filesystems: disko already declares fileSystems and swapDevices for
  # every partition it manages (via disko.nix). Without this flag,
  # nixos-generate-config also emits a fileSystems."/" block keyed by UUID,
  # which conflicts with disko's by-partlabel definition and fails the build
  # with: The option `fileSystems."/".device' has conflicting definition values.
  _simple_step "Generating hardware configuration..." \
    nixos-generate-config --no-filesystems --root /mnt

  _simple_step "Writing Kelvin configuration..." \
    generate_kelvin_config_simple

  _simple_step "Building system (this takes a while — seriously, go get that drink)..." \
    nixos-install --root /mnt --flake "/mnt/home/${S_USERNAME}/.kelvin/#kelvin" --no-root-passwd

  _simple_step "Setting password..." \
    bash -c "echo '${S_USERNAME}:${S_PASSWORD}' | nixos-enter --root /mnt -- chpasswd"

  return 0
}

# ─────────────────────────────────────────────────────────────────────────────
# Screen 8 — Done
# ─────────────────────────────────────────────────────────────────────────────

simple_screen_done() {
  clear

  gum style \
    --foreground "$KELVIN_WHITE" \
    --background "$KELVIN_BLUE" \
    --border double \
    --border-foreground "$KELVIN_ICE" \
    --padding "2 4" \
    --align center \
    --width 60 \
    "❄️  K E L V I N  ❄️" \
    "" \
    "you're all set! Kelvin is installed." \
    "your computer will restart in a moment." \
    "" \
    "welcome home. 🏠"

  echo
  gum confirm \
    --affirmative "Restart now" \
    --negative "Stay in live environment" \
    && reboot || true
}

# ─────────────────────────────────────────────────────────────────────────────
# Main flow
# ─────────────────────────────────────────────────────────────────────────────

run_simple_install() {
  simple_screen_welcome
  simple_screen_usecases
  simple_screen_identity
  simple_screen_locale
  simple_screen_disk

  if simple_screen_confirm; then
    # simple_screen_installing handles its own failures (it drops to a shell),
    # so it only returns success once the whole install has completed. Guard the
    # done screen on that success so a failed install can never fall through to
    # "you're all set!".
    if simple_screen_installing; then
      simple_screen_done
    fi
  else
    # User backed out — loop back to disk selection
    run_simple_install
  fi
}
