{ config, pkgs, lib, kelvinCfg, ... }:

{
  programs.zsh = {
    enable                    = true;
    autosuggestion.enable     = true;
    syntaxHighlighting.enable = true;
    historySize               = 50000;
    history.share             = true;

    oh-my-zsh = {
      enable  = true;
      theme   = "robbyrussell";
      plugins = [
        "git" "fzf" "z" "colored-man-pages"
        "command-not-found"
      ] ++ lib.optionals kelvinCfg.useCases.development [
        "docker" "docker-compose" "node" "python"
      ];
    };

    shellAliases = {
      # Modern replacements
      ls   = "eza --icons";
      ll   = "eza -la --icons --git";
      la   = "eza -a --icons";
      lt   = "eza --tree --icons --level=2";
      cat  = "bat --paging=never";
      grep = "rg";
      find = "fd";

      # Navigation
      ".."   = "cd ..";
      "..."  = "cd ../..";
      "...." = "cd ../../..";

      # Git shortcuts
      g   = "git";
      gs  = "git status";
      ga  = "git add";
      gc  = "git commit";
      gp  = "git push";
      gl  = "git log --oneline --graph --decorate";

      # Kelvin shortcuts
      ku  = "kelvin update";
      kr  = "kelvin rollback";
      ks  = "kelvin status";
      kc  = "kelvin clean";
      kd  = "kelvin doctor";
      kst = "kelvin-store";

      # Nix shortcuts
      nr   = "sudo nixos-rebuild switch --flake ~/.kelvin/#kelvin";
      nrt  = "sudo nixos-rebuild test --flake ~/.kelvin/#kelvin";
      ngc  = "sudo nix-collect-garbage --delete-older-than 14d";
      nup  = "nix flake update ~/.kelvin/";
    };

    initExtra = ''
      # Kelvin ZSH config
      # ─────────────────────────────────────────────────────────────
      # Add your custom configuration below.
      # This file is managed by Nix — persistent changes go in:
      #   ~/.kelvin/home/zsh.nix
      # ─────────────────────────────────────────────────────────────

      # zoxide (smarter cd) — must come after oh-my-zsh
      eval "$(zoxide init zsh)"

      # fzf keybindings + completion
      source ${pkgs.fzf}/share/fzf/key-bindings.zsh
      source ${pkgs.fzf}/share/fzf/completion.zsh

      # bat as MANPAGER
      export MANPAGER="sh -c 'col -bx | bat -l man -p'"

      # Show fastfetch on new terminal (can remove if annoying)
      if [[ $SHLVL -eq 1 ]]; then
        fastfetch --logo small
      fi
    '';
  };
}
