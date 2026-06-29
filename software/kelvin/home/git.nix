{ config, pkgs, lib, kelvinCfg, ... }:

{
  programs.git = {
    enable    = true;
    userName  = kelvinCfg.fullName;
    userEmail = kelvinCfg.email;

    extraConfig = {
      init.defaultBranch    = "main";
      pull.rebase           = true;
      push.autoSetupRemote  = true;
      core.editor           = if kelvinCfg.useCases.development then "code --wait" else "nano";
      core.autocrlf         = "input";
      diff.colorMoved       = "default";
      merge.conflictstyle   = "zdiff3";
      rerere.enabled        = true;

      # Nicer diffs
      delta = {
        enable         = true;
        navigate       = true;
        light          = false;
        side-by-side   = true;
        line-numbers   = true;
      };
    };

    aliases = {
      st  = "status";
      co  = "checkout";
      br  = "branch";
      unstage = "reset HEAD --";
      last    = "log -1 HEAD";
      lg      = "log --oneline --graph --decorate --all";
      wip     = "commit -am 'wip'";
    };
  };

  # delta — better git diff pager
  home.packages = [ pkgs.delta ];
}
