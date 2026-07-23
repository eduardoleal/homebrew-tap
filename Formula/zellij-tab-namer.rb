class ZellijTabNamer < Formula
  include Language::Python::Virtualenv

  desc "Name Zellij tabs from pane titles and lightweight local context"
  homepage "https://github.com/eduardoleal/zellij-tab-namer"
  github_token = ENV.fetch("HOMEBREW_GITHUB_API_TOKEN", nil)
  github_api_headers = [
    "Accept: application/vnd.github+json",
    "X-GitHub-Api-Version: 2022-11-28",
  ]
  github_api_headers << "Authorization: Bearer #{github_token}" if github_token

  url "https://api.github.com/repos/eduardoleal/zellij-tab-namer/tarball/v0.2.0",
      headers: github_api_headers
  sha256 "3aed8e67cbac7f57462b8de9b494fecdf7f15d9efabfc931c79307019d812e16"

  depends_on "python@3.14"

  resource "wasm" do
    url "https://api.github.com/repos/eduardoleal/zellij-tab-namer/releases/assets/486520223",
        headers: [
          "Accept: application/octet-stream",
          "X-GitHub-Api-Version: 2022-11-28",
          *("Authorization: Bearer #{github_token}" if github_token),
        ].compact
    sha256 "e6f4eb2f404a86dd27cb318d4ce4365869e44ca578b30e1a33932bc73682465b"
  end

  def install
    virtualenv_install_with_resources without: "wasm"
    resource("wasm").stage do
      (libexec/"plugin").install "zellij-tab-namer.wasm"
    end
  end

  def caveats
    <<~EOS
      Install and configure the native plugin with:
        zellij-tab-namer install --mode wasm --wasm-source "#{opt_libexec}/plugin/zellij-tab-namer.wasm"

      Then stop all Zellij sessions from outside Zellij so the new plugin and
      permission grants are loaded:
        zellij delete-all-sessions --force
    EOS
  end

  test do
    assert_match "usage:", shell_output("#{bin}/zellij-tab-namer --help")
    assert_equal "\0asm".b, (libexec/"plugin/zellij-tab-namer.wasm").binread(4)
  end
end
