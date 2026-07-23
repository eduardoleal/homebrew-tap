# Homebrew Tap

Homebrew formulae for `eduardoleal` projects.

## zellij-tab-namer

The formula installs the `zellij-tab-namer` management CLI and the native
headless WASM plugin:

```sh
brew install eduardoleal/tap/zellij-tab-namer
```

Homebrew prints the one-time command that adds the plugin to Zellij's config
and pre-grants its required headless permissions. To print it again later:

```sh
brew info eduardoleal/tap/zellij-tab-namer
```

The formula installs the checksum-pinned v0.2.0 source archive and published
WASM release asset. It does not build the plugin locally or edit
`~/.config/zellij` during `brew install`.

CI downloads and tests the public upstream release.
