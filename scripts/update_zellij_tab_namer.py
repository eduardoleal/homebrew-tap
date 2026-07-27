#!/usr/bin/env python3
"""Update the zellij-tab-namer formula from a verified GitHub release."""

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple


UPSTREAM_REPOSITORY = "eduardoleal/zellij-tab-namer"
WASM_NAME = "zellij-tab-namer.wasm"
CHECKSUM_NAME = f"{WASM_NAME}.sha256"
VERSION_RE = re.compile(r"^(?:v)?(\d+)\.(\d+)\.(\d+)$")
SOURCE_RE = re.compile(
    r'(?m)^(  url "https://github\.com/eduardoleal/zellij-tab-namer/'
    r"archive/refs/tags/v)(?P<version>\d+\.\d+\.\d+)"
    r'(\.tar\.gz"\n  sha256 ")(?P<sha>[^"]+)(")$'
)
WASM_RE = re.compile(
    r'(?m)^(  resource "wasm" do\n'
    r'    url "https://github\.com/eduardoleal/zellij-tab-namer/'
    r"releases/download/v)(?P<version>\d+\.\d+\.\d+)"
    r'(/zellij-tab-namer\.wasm"\n    sha256 ")(?P<sha>[^"]+)(")$'
)


class FormulaError(RuntimeError):
    """The managed formula no longer has the expected safe structure."""


class ReleaseNotReady(RuntimeError):
    """The upstream release exists but is not complete enough to package."""


class IntegrityError(RuntimeError):
    """A published release artifact failed integrity validation."""


@dataclass(frozen=True)
class Release:
    version: str
    wasm_url: str
    checksum_url: str


def normalize_version(value: str) -> Tuple[str, Tuple[int, int, int]]:
    match = VERSION_RE.fullmatch(value)
    if not match:
        raise FormulaError(f"unsupported stable release version: {value!r}")
    parts = tuple(int(part) for part in match.groups())
    return ".".join(str(part) for part in parts), parts


def parse_release(payload: Dict[str, object]) -> Release:
    if payload.get("draft") or payload.get("prerelease"):
        raise ReleaseNotReady("draft and prerelease versions are not packaged")

    version, _ = normalize_version(str(payload.get("tag_name", "")))
    asset_urls: Dict[str, str] = {}
    for raw_asset in payload.get("assets", []):
        if not isinstance(raw_asset, dict):
            continue
        name = raw_asset.get("name")
        url = raw_asset.get("browser_download_url")
        if name in (WASM_NAME, CHECKSUM_NAME) and isinstance(url, str):
            if name in asset_urls:
                raise IntegrityError(f"release has duplicate {name} assets")
            asset_urls[name] = url

    missing = [name for name in (WASM_NAME, CHECKSUM_NAME) if name not in asset_urls]
    if missing:
        raise ReleaseNotReady(
            "release assets are still incomplete: " + ", ".join(missing)
        )

    return Release(
        version=version,
        wasm_url=asset_urls[WASM_NAME],
        checksum_url=asset_urls[CHECKSUM_NAME],
    )


def verify_wasm_checksum(wasm: bytes, published_checksum: bytes) -> str:
    if not wasm.startswith(b"\0asm"):
        raise IntegrityError("downloaded release asset is not a WASM module")

    try:
        checksum_line = published_checksum.decode("ascii").strip()
    except UnicodeDecodeError as error:
        raise IntegrityError("published WASM checksum is not ASCII") from error

    match = re.fullmatch(
        rf"(?P<sha>[0-9a-fA-F]{{64}})\s+\*?{re.escape(WASM_NAME)}",
        checksum_line,
    )
    if not match:
        raise IntegrityError("published WASM checksum has an unexpected format")

    actual = hashlib.sha256(wasm).hexdigest()
    published = match.group("sha").lower()
    if actual != published:
        raise IntegrityError("published WASM checksum does not match the asset")
    return actual


def update_formula(
    formula: str,
    *,
    version: str,
    source_sha: str,
    wasm_sha: str,
) -> Tuple[str, bool]:
    normalized, target_parts = normalize_version(version)
    current_source, current_parts = formula_version(formula)
    if target_parts < current_parts:
        raise FormulaError(
            f"refusing to downgrade formula from {current_source} to {normalized}"
        )

    def replace_source(match: re.Match) -> str:
        return (
            match.group(1)
            + normalized
            + match.group(3)
            + source_sha
            + match.group(5)
        )

    def replace_wasm(match: re.Match) -> str:
        return (
            match.group(1)
            + normalized
            + match.group(3)
            + wasm_sha
            + match.group(5)
        )

    updated = SOURCE_RE.sub(replace_source, formula)
    updated = WASM_RE.sub(replace_wasm, updated)
    return updated, updated != formula


def formula_version(formula: str) -> Tuple[str, Tuple[int, int, int]]:
    source_matches = list(SOURCE_RE.finditer(formula))
    wasm_matches = list(WASM_RE.finditer(formula))
    if len(source_matches) != 1 or len(wasm_matches) != 1:
        raise FormulaError(
            "formula must contain exactly one managed source and WASM resource"
        )

    current_source = source_matches[0].group("version")
    current_wasm = wasm_matches[0].group("version")
    if current_source != current_wasm:
        raise FormulaError("formula source and WASM resource versions disagree")
    return normalize_version(current_source)


def api_json(url: str, token: Optional[str]) -> Dict[str, object]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "homebrew-tap-zellij-tab-namer-bump",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise ReleaseNotReady("requested GitHub release does not exist") from error
        raise


def download(url: str) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": "homebrew-tap-zellij-tab-namer-bump"}
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise ReleaseNotReady("release asset is not available yet") from error
        raise


def write_output(path: Optional[str], **values: object) -> None:
    if not path:
        return
    with Path(path).open("a", encoding="utf-8") as output:
        for key, value in values.items():
            output.write(f"{key}={str(value).lower() if isinstance(value, bool) else value}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--formula",
        default="Formula/zellij-tab-namer.rb",
        type=Path,
    )
    parser.add_argument("--repository", default=UPSTREAM_REPOSITORY)
    parser.add_argument("--version")
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    args = parser.parse_args()

    requested_version = None
    if args.version:
        requested_version, _ = normalize_version(args.version)
        endpoint = f"releases/tags/v{requested_version}"
    else:
        endpoint = "releases/latest"

    api_url = f"https://api.github.com/repos/{args.repository}/{endpoint}"
    try:
        release = parse_release(api_json(api_url, os.environ.get("GH_TOKEN")))
        if requested_version and release.version != requested_version:
            raise FormulaError(
                f"requested {requested_version}, received {release.version}"
            )

        original = args.formula.read_text(encoding="utf-8")
        current_version, current_parts = formula_version(original)
        _, release_parts = normalize_version(release.version)
        if current_parts > release_parts:
            message = (
                f"formula {current_version} is newer than release {release.version}"
            )
            if requested_version:
                raise FormulaError(message)
            print(f"Skipping: {message}")
            write_output(
                args.github_output,
                changed=False,
                status="skipped",
                version=release.version,
            )
            return 0
        if current_parts == release_parts:
            print(f"zellij-tab-namer {release.version}: formula is current")
            write_output(
                args.github_output,
                changed=False,
                status="current",
                version=release.version,
            )
            return 0

        source_url = (
            f"https://github.com/{args.repository}/archive/refs/tags/"
            f"v{release.version}.tar.gz"
        )
        source = download(source_url)
        if not source.startswith(b"\x1f\x8b"):
            raise IntegrityError("downloaded source archive is not gzip data")
        source_sha = hashlib.sha256(source).hexdigest()

        wasm = download(release.wasm_url)
        published_checksum = download(release.checksum_url)
        wasm_sha = verify_wasm_checksum(wasm, published_checksum)
    except ReleaseNotReady as error:
        print(f"Release not ready: {error}")
        write_output(
            args.github_output,
            changed=False,
            status="not-ready",
            version=requested_version or "",
        )
        return 0

    updated, changed = update_formula(
        original,
        version=release.version,
        source_sha=source_sha,
        wasm_sha=wasm_sha,
    )
    if changed:
        args.formula.write_text(updated, encoding="utf-8")

    status = "updated" if changed else "current"
    print(f"zellij-tab-namer {release.version}: formula is {status}")
    write_output(
        args.github_output,
        changed=changed,
        status=status,
        version=release.version,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
