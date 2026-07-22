# Homebrew Tap

Private Homebrew formulae for `eduardoleal` projects.

## zellij-tab-namer

The formula installs the `zellij-tab-namer` management CLI and the native
headless WASM plugin. Both this tap and the upstream repository are private, so
authenticate Git before installing:

```sh
gh auth login
gh auth setup-git
brew install eduardoleal/tap/zellij-tab-namer
```

Homebrew prints the one-time command that adds the plugin to Zellij's config
and pre-grants its required headless permissions. To print it again later:

```sh
brew info eduardoleal/tap/zellij-tab-namer
```

The formula builds from the immutable upstream tag and pinned revision. It
does not edit `~/.config/zellij` during `brew install`.
