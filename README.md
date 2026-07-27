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

The formula installs a checksum-pinned source archive and published WASM
release asset. It does not build the plugin locally or edit
`~/.config/zellij` during `brew install`.

CI downloads and tests the public upstream release.

## Automated updates

The `Bump zellij-tab-namer` workflow checks the latest stable upstream release
hourly. When a new version is available, it verifies the published WASM
checksum, recomputes the source archive checksum, and opens or updates a
formula bump pull request. It then dispatches the tap test workflow on that
branch.

The workflow can also be run manually, optionally for a specific stable
version:

```sh
gh workflow run bump-zellij-tab-namer.yml \
  --repo eduardoleal/homebrew-tap \
  -f version=0.4.0
```
