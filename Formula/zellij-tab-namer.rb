class ZellijTabNamer < Formula
  include Language::Python::Virtualenv

  desc "Name Zellij tabs from pane titles and lightweight local context"
  homepage "https://github.com/eduardoleal/zellij-tab-namer"

  url "https://github.com/eduardoleal/zellij-tab-namer/archive/refs/tags/v0.4.0.tar.gz"
  sha256 "05d7a434189d135c6a888bf966eb9e2c91650725cd8a9329ea5afd8f4eded62b"

  depends_on "python@3.14"

  resource "wasm" do
    url "https://github.com/eduardoleal/zellij-tab-namer/releases/download/v0.4.0/zellij-tab-namer.wasm"
    sha256 "e93cc21938636a753436d5fb3ebc5ec542903e3aaa4578263fdfebf3a26f5db8"
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
