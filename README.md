# Homebrew Tap

Private Homebrew formulae for `eduardoleal` projects.

## zellij-tab-namer

The formula installs the `zellij-tab-namer` management CLI and the native
headless WASM plugin. Both this tap and the upstream repository are private, so
the tap needs SSH access and Homebrew needs a GitHub token with read access to
the upstream repository:

```sh
export HOMEBREW_GITHUB_API_TOKEN="your-fine-grained-github-token"
brew tap eduardoleal/tap git@github.com:eduardoleal/homebrew-tap.git
brew install eduardoleal/tap/zellij-tab-namer
```

The token can be created in GitHub's web settings and does not require the
GitHub CLI. Grant it read-only access to the private `zellij-tab-namer`
repository.

Homebrew prints the one-time command that adds the plugin to Zellij's config
and pre-grants its required headless permissions. To print it again later:

```sh
brew info eduardoleal/tap/zellij-tab-namer
```

The formula installs the checksum-pinned v0.2.0 source archive and published
WASM release asset. It does not build the plugin locally or edit
`~/.config/zellij` during `brew install`.

CI uses a repository-scoped token to download and test the private upstream
release. Dependabot pull requests run the syntax gate only because GitHub does
not expose Actions secrets to Dependabot.
