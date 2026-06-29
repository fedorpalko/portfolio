#!/usr/bin/env python3
"""
Kelvin System Manager
A Rich-powered TUI for managing your Kelvin NixOS installation.

Usage:
    kelvin              # open full TUI dashboard
    kelvin update       # pull new nixpkgs, rebuild
    kelvin rollback     # list generations, pick one, switch
    kelvin status       # current gen, last update, nix store disk usage
    kelvin clean        # garbage collect old generations (with confirmation)
    kelvin doctor       # check for common config issues
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

# ── Kelvin brand colors ───────────────────────────────────────────────────────

KELVIN_BLUE  = "#A8D8EA"
KELVIN_WHITE = "#F5F5F5"
KELVIN_DARK  = "#2A2A2A"
KELVIN_ICE   = "#5BA4CF"

console = Console()

KELVIN_DIR = Path.home() / ".kelvin"
FLAKE_PATH = str(KELVIN_DIR)
FLAKE_TARGET = f"{FLAKE_PATH}#kelvin"

# ── Helpers ───────────────────────────────────────────────────────────────────

def run(cmd: list[str], capture: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=capture, text=True, check=check)

def kelvin_header() -> Panel:
    title = Text("❄  K E L V I N", style=f"bold {KELVIN_BLUE}")
    subtitle = Text("system manager", style=f"dim {KELVIN_WHITE}")
    return Panel(
        Text.assemble(title, "\n", subtitle),
        box=box.ROUNDED,
        border_style=KELVIN_ICE,
        padding=(0, 2),
    )

def get_current_generation() -> dict:
    """Return info about the current NixOS generation."""
    try:
        result = run(["nixos-version", "--json"], check=False)
        version = result.stdout.strip() if result.returncode == 0 else "unknown"
    except FileNotFoundError:
        version = "unknown"

    # Current generation symlink
    gen_link = Path("/nix/var/nix/profiles/system")
    gen_number = "?"
    gen_date = "?"

    if gen_link.exists():
        target = str(gen_link.resolve())
        parts = target.split("-")
        for i, p in enumerate(parts):
            if p.isdigit() and i > 0:
                gen_number = p
                break
        try:
            gen_date = datetime.fromtimestamp(gen_link.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass

    return {"version": version, "number": gen_number, "date": gen_date}

def get_nix_store_size() -> str:
    """Return nix store disk usage as a human-readable string."""
    try:
        result = run(["du", "-sh", "/nix/store"], check=False)
        return result.stdout.split()[0] if result.returncode == 0 else "?"
    except Exception:
        return "?"

def list_generations() -> list[dict]:
    """Return list of NixOS generations."""
    try:
        result = run(["nix-env", "--list-generations", "-p", "/nix/var/nix/profiles/system"])
        gens = []
        for line in result.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                gens.append({
                    "number": parts[0],
                    "date": " ".join(parts[1:3]) if len(parts) >= 3 else parts[1],
                    "current": "(current)" in line,
                })
        return gens
    except Exception:
        return []

# ── Commands ──────────────────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Kelvin system manager. Run without arguments to open the TUI dashboard."""
    if ctx.invoked_subcommand is None:
        dashboard()

def dashboard():
    """Full TUI dashboard showing system status and quick actions."""
    console.clear()
    console.print(kelvin_header())
    console.print()

    gen = get_current_generation()
    store_size = get_nix_store_size()

    # Status table
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("key",   style=f"dim {KELVIN_ICE}", no_wrap=True)
    table.add_column("value", style=KELVIN_WHITE)

    table.add_row("Generation", gen["number"])
    table.add_row("Built",      gen["date"])
    table.add_row("NixOS",      gen["version"])
    table.add_row("Store size", store_size)
    table.add_row("Config",     str(KELVIN_DIR))

    console.print(Panel(table, title="[bold]status[/bold]", border_style=KELVIN_ICE))
    console.print()

    # Quick actions menu
    console.print(f"  [{KELVIN_ICE}]kelvin update[/]    — pull new nixpkgs and rebuild")
    console.print(f"  [{KELVIN_ICE}]kelvin rollback[/]  — switch to a previous generation")
    console.print(f"  [{KELVIN_ICE}]kelvin clean[/]     — garbage collect old generations")
    console.print(f"  [{KELVIN_ICE}]kelvin doctor[/]    — check for config issues")
    console.print(f"  [{KELVIN_ICE}]kelvin-store[/]     — install or remove packages")
    console.print()

@cli.command()
def update():
    """Pull latest nixpkgs and rebuild the system."""
    console.print(kelvin_header())
    console.print()

    if not KELVIN_DIR.exists():
        console.print(f"[red]Error:[/red] ~/.kelvin not found. Is Kelvin installed?")
        sys.exit(1)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Updating flake inputs...", total=None)
        try:
            run(["nix", "flake", "update", FLAKE_PATH], capture=False)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]flake update failed:[/red] {e}")
            sys.exit(1)

        progress.update(task, description="Rebuilding system (this may take a while)...")
        try:
            run(["sudo", "nixos-rebuild", "switch", "--flake", FLAKE_TARGET], capture=False)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]nixos-rebuild failed:[/red] {e}")
            sys.exit(1)

    console.print(f"\n[{KELVIN_BLUE}]✓ System updated.[/{KELVIN_BLUE}]")

@cli.command()
def rollback():
    """List all generations and switch to a selected one."""
    console.print(kelvin_header())
    console.print()

    gens = list_generations()
    if not gens:
        console.print("[red]No generations found.[/red]")
        sys.exit(1)

    table = Table(box=box.SIMPLE, show_header=True)
    table.add_column("#",       style=KELVIN_ICE, justify="right")
    table.add_column("Date",    style=KELVIN_WHITE)
    table.add_column("",       style=f"dim {KELVIN_BLUE}")

    for g in gens:
        table.add_row(g["number"], g["date"], "← current" if g["current"] else "")

    console.print(table)
    console.print()

    gen_num = click.prompt("  Switch to generation #", type=str)

    if not Confirm.ask(f"  Switch to generation {gen_num}?"):
        console.print("  Cancelled.")
        return

    try:
        run(["sudo", "nix-env", "--switch-generation", gen_num,
             "-p", "/nix/var/nix/profiles/system"], capture=False)
        run(["sudo", "/nix/var/nix/profiles/system/bin/switch-to-configuration", "switch"],
            capture=False)
        console.print(f"\n[{KELVIN_BLUE}]✓ Switched to generation {gen_num}.[/{KELVIN_BLUE}]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Rollback failed:[/red] {e}")
        sys.exit(1)

@cli.command()
def status():
    """Show current generation info and nix store usage."""
    gen = get_current_generation()
    store_size = get_nix_store_size()

    console.print(kelvin_header())
    console.print()
    console.print(f"  Generation:  [{KELVIN_BLUE}]{gen['number']}[/{KELVIN_BLUE}]")
    console.print(f"  Built:       {gen['date']}")
    console.print(f"  NixOS:       {gen['version']}")
    console.print(f"  Store:       {store_size}")
    console.print(f"  Config:      {KELVIN_DIR}")
    console.print()

@cli.command()
def clean():
    """Garbage collect old generations with confirmation."""
    console.print(kelvin_header())
    console.print()

    gens = list_generations()
    old = [g for g in gens if not g["current"]]
    console.print(f"  Found [{KELVIN_ICE}]{len(gens)}[/{KELVIN_ICE}] total generations,"
                  f" [{KELVIN_ICE}]{len(old)}[/{KELVIN_ICE}] can be removed.\n")

    if not old:
        console.print("  Nothing to clean.")
        return

    if not Confirm.ask("  Delete old generations and run garbage collection?"):
        console.print("  Cancelled.")
        return

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("Removing old generations...", total=None)
        try:
            run(["sudo", "nix-collect-garbage", "--delete-older-than", "0d"], capture=False)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Clean failed:[/red] {e}")
            sys.exit(1)

    console.print(f"\n[{KELVIN_BLUE}]✓ Cleaned. Store is now {get_nix_store_size()}.[/{KELVIN_BLUE}]")

@cli.command()
def doctor():
    """Check for common Kelvin configuration issues."""
    console.print(kelvin_header())
    console.print()

    checks = []

    # Check ~/.kelvin exists
    checks.append(("~/.kelvin/ directory",    KELVIN_DIR.exists()))
    checks.append(("~/.kelvin/options.nix",   (KELVIN_DIR / "options.nix").exists()))
    checks.append(("~/.kelvin/flake.nix",     (KELVIN_DIR / "flake.nix").exists()))
    checks.append(("~/.kelvin/flake.lock",    (KELVIN_DIR / "flake.lock").exists()))
    checks.append(("nix flakes enabled",      _check_flakes_enabled()))
    checks.append(("nixos-rebuild available", _check_command("nixos-rebuild")))
    checks.append(("gum available",           _check_command("gum")))

    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("check",  style=KELVIN_WHITE, no_wrap=True)
    table.add_column("status", justify="left")

    all_ok = True
    for name, ok in checks:
        status_text = Text("✓ ok", style=f"bold {KELVIN_BLUE}") if ok else Text("✗ missing", style="bold red")
        table.add_row(name, status_text)
        if not ok:
            all_ok = False

    console.print(table)
    console.print()

    if all_ok:
        console.print(f"[{KELVIN_BLUE}]Everything looks good.[/{KELVIN_BLUE}]")
    else:
        console.print("[red]Some checks failed. See above.[/red]")
        sys.exit(1)

def _check_flakes_enabled() -> bool:
    try:
        result = run(["nix", "flake", "--help"], check=False)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def _check_command(cmd: str) -> bool:
    import shutil
    return shutil.which(cmd) is not None

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
