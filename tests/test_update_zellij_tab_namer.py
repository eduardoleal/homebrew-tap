import hashlib
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from scripts.update_zellij_tab_namer import (
    FormulaError,
    IntegrityError,
    ReleaseNotReady,
    download,
    formula_version,
    main,
    parse_release,
    update_formula,
    verify_wasm_checksum,
)


FORMULA = """\
class ZellijTabNamer < Formula
  url "https://github.com/eduardoleal/zellij-tab-namer/archive/refs/tags/v0.3.0.tar.gz"
  sha256 "source-old"

  resource "wasm" do
    url "https://github.com/eduardoleal/zellij-tab-namer/releases/download/v0.3.0/zellij-tab-namer.wasm"
    sha256 "wasm-old"
  end
end
"""


class ParseReleaseTests(unittest.TestCase):
    def test_accepts_stable_release_with_required_assets(self):
        release = parse_release(
            {
                "tag_name": "v0.4.0",
                "draft": False,
                "prerelease": False,
                "assets": [
                    {
                        "name": "zellij-tab-namer.wasm",
                        "browser_download_url": "https://example.test/plugin",
                    },
                    {
                        "name": "zellij-tab-namer.wasm.sha256",
                        "browser_download_url": "https://example.test/checksum",
                    },
                ],
            }
        )

        self.assertEqual("0.4.0", release.version)
        self.assertEqual("https://example.test/plugin", release.wasm_url)
        self.assertEqual("https://example.test/checksum", release.checksum_url)

    def test_treats_release_without_both_assets_as_not_ready(self):
        with self.assertRaises(ReleaseNotReady):
            parse_release(
                {
                    "tag_name": "v0.4.0",
                    "draft": False,
                    "prerelease": False,
                    "assets": [],
                }
            )


class ChecksumTests(unittest.TestCase):
    def test_accepts_matching_published_wasm_checksum(self):
        wasm = b"\0asm-release"
        digest = hashlib.sha256(wasm).hexdigest()

        self.assertEqual(
            digest,
            verify_wasm_checksum(
                wasm,
                f"{digest}  zellij-tab-namer.wasm\n".encode(),
            ),
        )

    def test_rejects_mismatched_published_wasm_checksum(self):
        with self.assertRaises(IntegrityError):
            verify_wasm_checksum(
                b"\0asm-release",
                f"{'0' * 64}  zellij-tab-namer.wasm\n".encode(),
            )

    def test_treats_missing_asset_download_as_not_ready(self):
        error = urllib.error.HTTPError(
            "https://example.test/plugin", 404, "Not Found", {}, None
        )
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(ReleaseNotReady):
                download("https://example.test/plugin")


class FormulaUpdateTests(unittest.TestCase):
    def test_real_formula_keeps_the_managed_shape(self):
        formula_path = (
            Path(__file__).resolve().parent.parent
            / "Formula"
            / "zellij-tab-namer.rb"
        )

        version, _ = formula_version(formula_path.read_text(encoding="utf-8"))

        self.assertRegex(version, r"^\d+\.\d+\.\d+$")

    def test_reads_the_single_managed_formula_version(self):
        version, parts = formula_version(FORMULA)

        self.assertEqual("0.3.0", version)
        self.assertEqual((0, 3, 0), parts)

    def test_updates_source_and_wasm_urls_and_checksums_together(self):
        updated, changed = update_formula(
            FORMULA,
            version="0.4.0",
            source_sha="source-new",
            wasm_sha="wasm-new",
        )

        self.assertTrue(changed)
        self.assertIn("refs/tags/v0.4.0.tar.gz", updated)
        self.assertIn('sha256 "source-new"', updated)
        self.assertIn("releases/download/v0.4.0/zellij-tab-namer.wasm", updated)
        self.assertIn('sha256 "wasm-new"', updated)
        self.assertNotIn("v0.3.0", updated)

    def test_is_idempotent_when_formula_already_matches(self):
        updated, _ = update_formula(
            FORMULA,
            version="0.4.0",
            source_sha="source-new",
            wasm_sha="wasm-new",
        )

        repeated, changed = update_formula(
            updated,
            version="0.4.0",
            source_sha="source-new",
            wasm_sha="wasm-new",
        )

        self.assertFalse(changed)
        self.assertEqual(updated, repeated)

    def test_rejects_formula_without_exact_managed_resource(self):
        with self.assertRaises(FormulaError):
            update_formula(
                FORMULA.replace('  resource "wasm" do', '  resource "plugin" do'),
                version="0.4.0",
                source_sha="source-new",
                wasm_sha="wasm-new",
            )


class MainTests(unittest.TestCase):
    @mock.patch("scripts.update_zellij_tab_namer.download")
    @mock.patch("scripts.update_zellij_tab_namer.api_json")
    def test_updates_formula_and_github_outputs_from_verified_release(
        self, api_json_mock, download_mock
    ):
        source = b"\x1f\x8bsource"
        wasm = b"\0asm-release"
        wasm_sha = hashlib.sha256(wasm).hexdigest()
        api_json_mock.return_value = {
            "tag_name": "v0.5.0",
            "draft": False,
            "prerelease": False,
            "assets": [
                {
                    "name": "zellij-tab-namer.wasm",
                    "browser_download_url": "https://example.test/plugin",
                },
                {
                    "name": "zellij-tab-namer.wasm.sha256",
                    "browser_download_url": "https://example.test/checksum",
                },
            ],
        }
        download_mock.side_effect = [
            source,
            wasm,
            f"{wasm_sha}  zellij-tab-namer.wasm\n".encode(),
        ]

        with tempfile.TemporaryDirectory() as directory:
            formula_path = Path(directory) / "zellij-tab-namer.rb"
            output_path = Path(directory) / "github-output"
            real_formula = (
                Path(__file__).resolve().parent.parent
                / "Formula"
                / "zellij-tab-namer.rb"
            )
            formula_path.write_text(
                real_formula.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            with mock.patch(
                "sys.argv",
                [
                    "update_zellij_tab_namer.py",
                    "--formula",
                    str(formula_path),
                    "--github-output",
                    str(output_path),
                ],
            ):
                self.assertEqual(0, main())

            updated = formula_path.read_text(encoding="utf-8")
            output = output_path.read_text(encoding="utf-8")

        self.assertIn("refs/tags/v0.5.0.tar.gz", updated)
        self.assertIn(hashlib.sha256(source).hexdigest(), updated)
        self.assertIn(wasm_sha, updated)
        self.assertIn("changed=true", output)
        self.assertIn("status=updated", output)
        self.assertIn("version=0.5.0", output)


if __name__ == "__main__":
    unittest.main()
