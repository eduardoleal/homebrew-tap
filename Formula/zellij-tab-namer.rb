class ZellijTabNamer < Formula
  include Language::Python::Virtualenv

  desc "Name Zellij tabs from pane titles and lightweight local context"
  homepage "https://github.com/eduardoleal/zellij-tab-namer"
  github_token = ENV.fetch("HOMEBREW_GITHUB_API_TOKEN", nil)
  github_asset_headers = [
    "Accept: application/octet-stream",
    "X-GitHub-Api-Version: 2022-11-28",
  ]
  github_asset_headers << "Authorization: Bearer #{github_token}" if github_token

  url "https://api.github.com/repos/eduardoleal/zellij-tab-namer/releases/assets/487141752",
      headers: github_asset_headers
  version "0.2.0"
  sha256 "f6de1526dac6a05fba4f33df398036be38226ef04d1c1ae3e182e7a74a3a982c"

  depends_on "python@3.14"

  resource "wasm" do
    url "https://api.github.com/repos/eduardoleal/zellij-tab-namer/releases/assets/486520223",
        headers: github_asset_headers
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
