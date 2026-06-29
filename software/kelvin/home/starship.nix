{ config, pkgs, lib, kelvinCfg, ... }:

{
  programs.starship = {
    enable = true;
    enableZshIntegration = true;

    settings = {
      # ── Prompt layout ──────────────────────────────────────────────────────
      format = lib.concatStrings [
        "[❄ ](bold #A8D8EA)"         # snowflake prefix
        "$username"
        "$hostname"
        "$directory"
        "$git_branch"
        "$git_status"
        "$python"
        "$nodejs"
        "$rust"
        "$nix_shell"
        "$cmd_duration"
        "$line_break"
        "$character"
      ];

      # ── Components ─────────────────────────────────────────────────────────

      character = {
        success_symbol = "[›](bold #A8D8EA)";
        error_symbol   = "[›](bold red)";
        vimcmd_symbol  = "[‹](bold #5BA4CF)";
      };

      directory = {
        style            = "bold #A8D8EA";
        truncation_length = 4;
        truncate_to_repo  = true;
        substitutions = {
          "~/.kelvin" = "❄ kelvin";
          "~"         = "~";
        };
      };

      username = {
        style_user = "#5BA4CF";
        style_root = "bold red";
        format     = "[$user]($style) ";
        show_always = false;  # only show when SSH'd in
      };

      hostname = {
        ssh_only = true;
        style    = "bold #5BA4CF";
        format   = "[@$hostname]($style) ";
      };

      git_branch = {
        style  = "#5BA4CF";
        symbol = " ";
        format = "[$symbol$branch]($style) ";
      };

      git_status = {
        style    = "#A8D8EA";
        format   = "([\\[$all_status$ahead_behind\\]]($style) )";
        ahead    = "⇡$count";
        behind   = "⇣$count";
        diverged = "⇕⇡$ahead_count⇣$behind_count";
        modified = "!$count";
        staged   = "+$count";
        untracked = "?$count";
        stashed  = "≡";
      };

      nix_shell = {
        style   = "bold #A8D8EA";
        symbol  = "❄ ";
        format  = "[$symbol$state( \\($name\\))]($style) ";
        impure_msg = "impure";
        pure_msg   = "pure";
      };

      python = {
        style  = "bold #A8D8EA";
        symbol = " ";
        format = "[$symbol$version( \\($virtualenv\\))]($style) ";
      };

      nodejs = {
        style  = "bold #A8D8EA";
        symbol = " ";
        format = "[$symbol$version]($style) ";
      };

      rust = {
        style  = "bold #A8D8EA";
        symbol = " ";
        format = "[$symbol$version]($style) ";
      };

      cmd_duration = {
        min_time   = 2000;
        style      = "dim #5BA4CF";
        format     = "[$duration]($style) ";
      };
    };
  };

  home.packages = [ pkgs.starship ];
}
