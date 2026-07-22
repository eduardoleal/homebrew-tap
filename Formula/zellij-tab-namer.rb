class ZellijTabNamer < Formula
  include Language::Python::Virtualenv

  desc "Name Zellij tabs from pane titles and lightweight local context"
  homepage "https://github.com/eduardoleal/zellij-tab-namer"
  url "https://github.com/eduardoleal/zellij-tab-namer.git",
      tag:      "v0.2.0",
      revision: "fa7ab9071f5448b28f4f37423efe370bf4e5971d"
  version "0.2.0"

  depends_on "rustup" => :build
  depends_on "python@3.14"

  def install
    rustup_home = buildpath/".rustup"
    cargo_home = buildpath/".cargo"
    ENV["RUSTUP_HOME"] = rustup_home
    ENV["CARGO_HOME"] = cargo_home

    system "rustup", "toolchain", "install", "1.97.1", "--profile", "minimal",
                     "--target", "wasm32-wasip1"
    # This package intentionally builds a WASM artifact, not a host binary.
    cargo_args = %w[cargo build --locked --release --target wasm32-wasip1
                    --bin zellij-tab-namer]
    system "rustup", "run", "1.97.1", *cargo_args

    virtualenv_install_with_resources
    (libexec/"plugin").install \
      "target/wasm32-wasip1/release/zellij-tab-namer.wasm"
  end

  def caveats
    <<~EOS
      Install and configure the native plugin with:
        zellij-tab-namer install --mode wasm \
          --wasm-source "#{opt_libexec}/plugin/zellij-tab-namer.wasm"

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
