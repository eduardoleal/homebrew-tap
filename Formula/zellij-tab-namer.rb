class ZellijTabNamer < Formula
  include Language::Python::Virtualenv

  desc "Name Zellij tabs from pane titles and lightweight local context"
  homepage "https://github.com/eduardoleal/zellij-tab-namer"

  url "https://github.com/eduardoleal/zellij-tab-namer/archive/refs/tags/v0.3.0.tar.gz"
  sha256 "4271d3ba5c4454190e3aa8272d8148a55577a016d6edc59f287e687a66766ffa"

  depends_on "python@3.14"

  resource "wasm" do
    url "https://github.com/eduardoleal/zellij-tab-namer/releases/download/v0.3.0/zellij-tab-namer.wasm"
    sha256 "4910509ac96bc7d604e07852fa6fc5e9a2427c5342a0cb76a721f5c0042b129c"
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
