#!/usr/bin/env python3
"""
Kelvin Store — package manager TUI
Search nixpkgs live, add/remove packages, rebuild.

Usage:
    kelvin-store          # open TUI
    kelvin-store search   <query>    # search without opening TUI
    kelvin-store install  <package>  # add package to packages.nix and rebuild
    kelvin-store remove   <package>  # remove package from packages.nix and rebuild
"""

import subprocess
import sys
import json
import re
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

# ── Brand ─────────────────────────────────────────────────────────────────────

KELVIN_BLUE  = "#A8D8EA"
KELVIN_WHITE = "#F5F5F5"
KELVIN_DARK  = "#2A2A2A"
KELVIN_ICE   = "#5BA4CF"

console = Console()

KELVIN_DIR    = Path.home() / ".kelvin"
PACKAGES_NIX  = KELVIN_DIR / "packages.nix"
FLAKE_TARGET  = f"{KELVIN_DIR}#kelvin"

# ── Helpers ───────────────────────────────────────────────────────────────────

def store_header() -> Panel:
    title = Text("❄  K E L V I N   S T O R E", style=f"bold {KELVIN_BLUE}")
    subtitle = Text("package manager", style=f"dim {KELVIN_WHITE}")
    return Panel(
        Text.assemble(title, "\n", subtitle),
        box=box.ROUNDED,
        border_style=KELVIN_ICE,
        padding=(0, 2),
    )

def nix_search(query: str) -> list[dict]:
    """Run nix search nixpkgs <query> and return parsed results."""
    try:
        result = subprocess.run(
            ["nix", "search", "nixpkgs", query, "--json"],
            capture_output=True, text=True, check=False, timeout=30,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []

        raw = json.loads(result.stdout)
        packages = []
        for attr, info in raw.items():
            # attr looks like "legacyPackages.x86_64-linux.htop"
            name = attr.split(".")[-1]
            packages.append({
                "attr":        name,
                "pname":       info.get("pname", name),
                "version":     info.get("version", ""),
                "description": info.get("description", ""),
            })
        return packages[:50]  # cap results for readability

    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        console.print(f"[red]Search error:[/red] {e}")
        return []

def read_packages_nix() -> list[str]:
    """Extract the list of user-added packages from packages.nix."""
    if not PACKAGES_NIX.exists():
        return []

    content = PACKAGES_NIX.read_text()
    # Look for the kelvin-store managed block
    match = re.search(
        r"# KELVIN-STORE-BEGIN(.*?)# KELVIN-STORE-END",
        content, re.DOTALL
    )
    if not match:
        return []

    block = match.group(1)
    pkgs = re.findall(r"^\s+([\w-]+)", block, re.MULTILINE)
    return pkgs

def write_user_packages(packages: list[str]) -> None:
    """Write the kelvin-store managed block into packages.nix."""
    if not PACKAGES_NIX.exists():
        # Create a minimal packages.nix
        PACKAGES_NIX.write_text(
            "# ~/.kelvin/packages.nix — user packages added via kelvin-store\n"
            "{ pkgs, ... }:\n{\n"
            "  environment.systemPackages = with pkgs; [\n"
            "    # KELVIN-STORE-BEGIN\n"
            "    # KELVIN-STORE-END\n"
            "  ];\n"
            "}\n"
        )

    content = PACKAGES_NIX.read_text()

    new_block = "    # KELVIN-STORE-BEGIN\n"
    for pkg in sorted(set(packages)):
        new_block += f"    {pkg}\n"
    new_block += "    # KELVIN-STORE-END"

    new_content = re.sub(
        r"    # KELVIN-STORE-BEGIN.*?    # KELVIN-STORE-END",
        new_block,
        content,
        flags=re.DOTALL,
    )
    PACKAGES_NIX.write_text(new_content)

def rebuild_now() -> bool:
    """Ask user whether to rebuild now, and do so if yes."""
    console.print()
    if Confirm.ask("  Rebuild now?"):
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            progress.add_task("Rebuilding system...", total=None)
            try:
                subprocess.run(
                    ["sudo", "nixos-rebuild", "switch", "--flake", FLAKE_TARGET],
                    check=True,
                )
                return True
            except subprocess.CalledProcessError as e:
                console.print(f"[red]Rebuild failed:[/red] {e}")
                return False
    else:
        console.print(f"  [{KELVIN_ICE}]Skipped. Run 'kelvin update' later to apply changes.[/{KELVIN_ICE}]")
        return True

# ── Commands ──────────────────────────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Kelvin Store — search and install packages from nixpkgs."""
    if ctx.invoked_subcommand is None:
        tui_main()

def tui_main():
    """Interactive TUI: search → select → install/remove."""
    console.clear()
    console.print(store_header())
    console.print()

    current = read_packages_nix()
    if current:
        console.print(f"  Currently installed via store: [{KELVIN_ICE}]{', '.join(current)}[/{KELVIN_ICE}]")
        console.print()

    query = Prompt.ask("  Search nixpkgs", default="")
    if not query:
        console.print("  No query entered.")
        return

    console.print()
    with Progress(SpinnerColumn(), TextColumn(f"Searching nixpkgs for '{query}'..."), console=console) as p:
        p.add_task("", total=None)
        results = nix_search(query)

    if not results:
        console.print(f"  [dim]No results for '{query}'.[/dim]")
        return

    # Display results
    table = Table(box=box.SIMPLE, show_header=True, header_style=f"bold {KELVIN_ICE}")
    table.add_column("#",       justify="right", style=KELVIN_ICE, no_wrap=True)
    table.add_column("Package", style=f"bold {KELVIN_WHITE}", no_wrap=True)
    table.add_column("Version", style="dim", no_wrap=True)
    table.add_column("Description", style=KELVIN_WHITE)

    for i, pkg in enumerate(results, 1):
        installed = " [installed]" if pkg["attr"] in current else ""
        table.add_row(
            str(i),
            pkg["attr"] + installed,
            pkg["version"],
            pkg["description"][:70],
        )

    console.print(table)
    console.print()

    choice = Prompt.ask("  Enter package number to install/remove (or 'q' to quit)", default="q")
    if choice.lower() == "q":
        return

    try:
        idx = int(choice) - 1
        pkg = results[idx]
    except (ValueError, IndexError):
        console.print("[red]Invalid selection.[/red]")
        return

    attr = pkg["attr"]

    if attr in current:
        if Confirm.ask(f"  Remove [{KELVIN_BLUE}]{attr}[/{KELVIN_BLUE}]?"):
            current.remove(attr)
            write_user_packages(current)
            console.print(f"  [{KELVIN_BLUE}]✓ Removed {attr}.[/{KELVIN_BLUE}]")
            rebuild_now()
    else:
        if Confirm.ask(f"  Install [{KELVIN_BLUE}]{attr}[/{KELVIN_BLUE}]?"):
            current.append(attr)
            write_user_packages(current)
            console.print(f"  [{KELVIN_BLUE}]✓ Added {attr} to packages.nix.[/{KELVIN_BLUE}]")
            rebuild_now()

@cli.command()
@click.argument("query")
def search(query):
    """Search nixpkgs for a package."""
    console.print(store_header())
    console.print()

    with Progress(SpinnerColumn(), TextColumn(f"Searching for '{query}'..."), console=console) as p:
        p.add_task("", total=None)
        results = nix_search(query)

    if not results:
        console.print(f"  [dim]No results for '{query}'.[/dim]")
        return

    table = Table(box=box.SIMPLE, header_style=f"bold {KELVIN_ICE}")
    table.add_column("Package", style=f"bold {KELVIN_WHITE}", no_wrap=True)
    table.add_column("Version", style="dim", no_wrap=True)
    table.add_column("Description", style=KELVIN_WHITE)

    for pkg in results:
        table.add_row(pkg["attr"], pkg["version"], pkg["description"][:80])

    console.print(table)

@cli.command()
@click.argument("package")
def install(package):
    """Add a package to packages.nix and optionally rebuild."""
    current = read_packages_nix()
    if package in current:
        console.print(f"  [{KELVIN_BLUE}]{package}[/{KELVIN_BLUE}] is already installed.")
        return
    current.append(package)
    write_user_packages(current)
    console.print(f"  [{KELVIN_BLUE}]✓ Added {package} to ~/.kelvin/packages.nix.[/{KELVIN_BLUE}]")
    rebuild_now()

@cli.command()
@click.argument("package")
def remove(package):
    """Remove a package from packages.nix and optionally rebuild."""
    current = read_packages_nix()
    if package not in current:
        console.print(f"  [{KELVIN_WHITE}]{package}[/{KELVIN_WHITE}] is not in your package list.")
        return
    current.remove(package)
    write_user_packages(current)
    console.print(f"  [{KELVIN_BLUE}]✓ Removed {package} from ~/.kelvin/packages.nix.[/{KELVIN_BLUE}]")
    rebuild_now()

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
