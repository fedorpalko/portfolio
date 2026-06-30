# Kelvin Build-Test-Fix Log

Autonomous build/test/fix loop for the Kelvin NixOS installer, run by Claude.

## Environment

- **No hardware virtualization available**: `/proc/cpuinfo` exposes no `vmx`/`svm`,
  `/dev/kvm` does not exist, and there is no passwordless sudo to load KVM modules.
  QEMU therefore runs under **TCG software emulation** (functional but slow).
- Strategy: catch the bulk of errors (Nix evaluation, package references, module
  options) with **fast host-native builds** (`nix build .#nixosConfigurations.kelvin
  ...toplevel` and `nix build .#iso`); reserve slow QEMU runs for the **install
  mechanics** (disko partitioning, hardware-config generation, the module-copy /
  flake.lock logic in generate.sh, bootloader install, first boot) that can only be
  exercised by a real install.

## Test harness

- `test-iso.sh` — improved: headless (`-display none`), serial console redirected to
  a log file (`-serial file:...`), automatic KVM→TCG fallback.
- `test/` — test-only autoinstall overlay (does NOT touch the shipped installer's
  copy/voice content): boots the ISO and runs the non-interactive install
  (disko + nixos-generate-config + generate_kelvin_config + nixos-install) with a
  fixed set of answers, logging everything to the serial console.

---

## Iterations

### Iteration 1 — host eval (`nixosConfigurations.kelvin` toplevel)

- **Error:** `error: 'libsForQt5.qt5.*' attributes were removed in favor of top-level
  'qt5.*' attributes` — while evaluating `environment.systemPackages` from
  `desktop/kde.nix`.
- **Cause:** nixpkgs removed the `libsForQt5.qt5.*` alias; `desktop/kde.nix:46`
  referenced `libsForQt5.qt5.qtwayland`.
- **Fix:** `desktop/kde.nix` — `libsForQt5.qt5.qtwayland` → `qt5.qtwayland`.

### Iteration 2 — host eval

- **Error:** `error: 'noto-fonts-emoji' has been renamed to/replaced by
  'noto-fonts-color-emoji'`.
- **Cause:** `desktop/fonts.nix:22` referenced the old package name.
- **Fix:** `desktop/fonts.nix` — `noto-fonts-emoji` → `noto-fonts-color-emoji`.

### Iteration 3 — host build (system assembly)

- **Error:** system builder fails: `The bootloader cannot find the proper kernel
  image. (Expecting /nix/store/…-linux-zen-7.0.12/bzImage)`.
- **Cause:** Upstream packaging regression in `linux-zen 7.0.12` (current nixpkgs):
  the kernel installs its image as **`vmlinuz`**, but `kernel.target` (which NixOS
  uses for `system.boot.loader.kernelFile`) still reports **`bzImage`**. Confirmed
  by inspecting the store outputs — zen ships `vmlinuz` (no `bzImage`), while LTS
  6.18 correctly ships `bzImage`. Kelvin defaults to the zen kernel, so this hits
  the default install path.
- **Fix:** `system/boot.nix` — `system.boot.loader.kernelFile = lib.mkIf
  (cfg.kernel == "zen") "vmlinuz";` so the loader points at the file the zen
  kernel actually produces. 6.x kernels keep the default `bzImage`. Documented as
  a removable upstream workaround.

### Iteration 4 — first QEMU boot (headless, serial)

- **Milestone:** ISO booted under TCG, autoinstall service started, reached the
  first install step.
- **Error:** `partition_disk_simple` failed instantly with rc=127; serial log:
  `/etc/kelvin-autoinstall.sh: line 66: bash: command not found`.
- **Cause:** TEST-HARNESS bug (not a Kelvin bug). The autoinstall runs as a
  systemd oneshot service, which starts with a minimal PATH lacking
  `/run/current-system/sw/bin`, so even `bash`/`disko`/`nixos-*` don't resolve.
  The real interactive installer runs from a login shell that has the full
  system profile on PATH.
- **Fix:** `test/autoinstall.sh` — export
  `PATH=/run/current-system/sw/bin:/run/wrappers/bin:/run/current-system/sw/sbin:$PATH`
  at the top so every command resolves, matching the interactive environment.

### Iteration 5 — QEMU boot (partitioning)

- **Milestone:** PATH fix worked; autoinstall reached and ran the partitioning
  step (disko actually executed this time).
- **Error (REAL Kelvin bug):** disko failed with
  `error: file 'nixpkgs' was not found in the Nix search path (add it using
  $NIX_PATH or -I)`.
- **Cause:** `partition_disk_simple` runs `disko --mode destroy,format,mount
  --yes-wipe-all-disks /tmp/kelvin-disko.nix` on a *plain, non-flake* disko file.
  disko evaluates it with `nix-instantiate`, which needs `<nixpkgs>` on the Nix
  search path. The flake-based ISO sets no channels, so `NIX_PATH` is empty and
  partitioning fails for everyone, not just the test. (Real installer bug.)
- **Fix:** `iso.nix` — `nix.nixPath = [ "nixpkgs=${pkgs.path}" ];` pins
  `<nixpkgs>` to the exact nixpkgs the ISO was built from, so disko can evaluate
  the disko file. ISO-only change; the installed system's flake is unaffected.

### Iteration 6 — QEMU boot (partitioning, again)

- **Observation:** Same `file 'nixpkgs' was not found` at partitioning. But
  inspecting the rebuilt ISO confirmed the iter-5 fix DID land:
  `set-environment` now exports `NIX_PATH="nixpkgs=/nix/store/…-source"`.
- **Cause (TEST-HARNESS):** `nix.nixPath` sets `NIX_PATH` via the login-shell
  profile (`/etc/set-environment`), and it does NOT write `nix-path` into
  `nix.conf`. The real interactive installer runs from a tty1 *login* shell, so
  it gets `NIX_PATH` and disko works. The autoinstall service did not run in a
  login shell, so it lacked `NIX_PATH`. (Real users are unaffected; this was the
  harness diverging from the real environment.)
- **Fix:** `test/iso-test.nix` — run autoinstall via `bash --login` so it sources
  `/etc/profile` + `/etc/set-environment`, replicating the real installer's
  login-shell PATH/NIX_PATH exactly.

### Iteration 7 — QEMU install reached nixos-install, guest died (OOM)

- **Milestone:** Big progress — 3 of 5 steps passed cleanly:
  Partitioning ✅, Hardware config ✅, Writing Kelvin config ✅ (incl. `flake
  lock` fetching all inputs). `nixos-install` started and ran ~15 min, copying
  the closure (host binary cache at 10.0.2.2:8000 confirmed in use).
- **Symptom:** Serial log truncated mid-line at ~1504s; QEMU exited rc=0 (clean
  guest reset under `-no-reboot`) with no result marker. ~600 MiB written to the
  target disk before death.
- **Cause (HOST/ENV, not Kelvin):** Host has only 11 GiB RAM with ~4.9 GiB
  available and swap already full. Guest was given 6 GiB, pushing the host to
  exhaustion; meanwhile the live ISO runs from a RAM-backed tmpfs, so the
  memory-heavy nixos-install eval/copy OOM-panicked the guest.
- **Fix (harness only):** `test-iso.sh` lowers default guest RAM to 4096 MB and
  attaches a sparse 12 GiB raw **swap disk** as `/dev/vdb` (host-file-backed, so
  it costs host disk not host RAM). `test/autoinstall.sh` runs `mkswap`+`swapon
  /dev/vdb` at startup so the guest (and its tmpfs) spills to disk instead of
  OOM-panicking. Disko still only ever touches the target disk (vda).



---

### Iteration 8 — KVM install (FAST), real bug in Development packages

- **Environment fix:** Enabled Intel VT-x in BIOS → `/dev/kvm` now present →
  QEMU runs with `-enable-kvm` (near-native). Also discovered `/tmp` is a 5.8 GiB
  **tmpfs (RAM-backed)** — moved the binary cache + VM disk + swap onto the SSD
  (`~/.cache/kelvin-vmtest`), freeing RAM and removing the disk-quota wall.
  Under KVM: boot ~11 s, partition ~20 s, config write ~42 s (vs minutes under TCG).
- **Error (REAL Kelvin bug):** `nixos-install` failed with
  `error: undefined variable 'npm'`.
- **Why host build missed it:** the host build used DEFAULT options (all
  use-cases off), so it never evaluated the use-case package lists. The VM
  install enables the **Development** use-case, which pulls in `packages.nix`'s
  dev list — `nodejs npm`, but there is no standalone `npm` attribute (npm ships
  inside `nodejs`).
- **Fix:** `packages.nix:43` — `nodejs npm` → `nodejs`.
- **Process fix:** added a host eval that enables EVERY use-case
  (`scratchpad/all-usecases.nix`) to flush all use-case package errors at once,
  instead of finding them one slow VM install at a time.

### Iteration 9 — flush ALL use-case package bugs on the host

Using `scratchpad/all-usecases.nix` (every use-case enabled) + `nix eval` to
surface errors fast, fixed in sequence until eval was clean (`EVAL_EXIT: 0`):

- `system/services.nix` — removed `virtualisation.libvirtd.qemu.ovmf.enable`
  (option removed upstream; OVMF ships with QEMU by default). Was an assertion
  failure under `useCases.virtualization`.
- `packages.nix` (media + creative) — `kdenlive` → `kdePackages.kdenlive`
  (moved under kdePackages in current nixpkgs).
- `packages.nix` (server) — removed `portainer` (not in nixpkgs; runs as a
  container).

Result: the full config now evaluates with **every** use-case enabled, so no
undefined-package/option errors remain on any install path. Then built the
**Development** toplevel on the host (eval ≠ build) and seeded it into the VM
binary cache so the install is fully local.

## Current status & how to resume (as of iteration 7 / run 5)

**Where we are:** All host-build bugs fixed; the full system config builds on the
host. In the VM, the installer clears partitioning, hardware-config generation,
and config writing; `nixos-install` is the remaining step to verify end-to-end.
A real-hardware USB test got all the way to `nixos-install` and only failed on a
flaky-internet package download (not a Kelvin bug).

**The bottleneck:** This host (ThinkPad T460s, i7-6600U) has Intel VT-x DISABLED
in BIOS, so QEMU runs under slow TCG software emulation. Enabling VT-x
(Security → Virtualization → Intel Virtualization Technology = Enabled) makes
`/dev/kvm` appear and the install run in minutes instead of hours.

**To resume after a reboot:**
1. `cd /home/quantman/Development/Projects/portfolio/software/kelvin`
2. Re-seed the local binary cache (only if /tmp was cleared):
   `SP=<scratchpad>; nix copy --to "file://$SP/bincache" \
      "$(nix build .#nixosConfigurations.kelvin.config.system.build.toplevel \
         --no-link --print-out-paths)"`
3. Build the test ISO: `nix build .#iso-test -o "$SP/result-iso-test"`
4. Run headless (auto-uses KVM if /dev/kvm exists):
   `KELVIN_HEADLESS=1 KELVIN_ISO=<iso> KELVIN_CACHE_DIR="$SP/bincache" \
    KELVIN_SERIAL_LOG="$SP/kelvin-boot.log" bash test-iso.sh`
5. Watch `KELVIN-TEST` markers in the serial log; success prints
   `KELVIN-TEST-RESULT: SUCCESS`.

**Production ISO already built** at `~/kelvin-installer.iso` (interactive
installer, all real fixes baked in) — ready to flash with
`sudo dd if=~/kelvin-installer.iso of=/dev/sdX bs=4M oflag=sync status=progress`.

### Iteration 10 — kernel image error (nixpkgs version skew), real fix

- **Error:** installed system build failed: `The bootloader cannot find the
  proper kernel image. (Expecting .../linux-zen-7.1.2/vmlinuz)`.
- **Root cause:** version skew. The installer locks the *latest* nixos-unstable
  (`b5aa0fb`, zen **7.1.2**), but the repo + my host tests used the older pinned
  `e73de5b` (zen **7.0.12**). Upstream FIXED the zen kernel between those commits
  — 7.1.2 ships `bzImage` again — so the iter-3 `kernelFile = "vmlinuz"`
  workaround now pointed at a nonexistent file.
- **Fix:** removed the `vmlinuz` override in `system/boot.nix` (default
  `bzImage` is correct for the fixed kernel) AND ran `nix flake update` so the
  repo locks the same `b5aa0fb` the installer uses — eliminating the skew so host
  builds match real installs. Verified: Development toplevel builds cleanly
  against `b5aa0fb`.
