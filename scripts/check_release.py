"""Inspect source/wheel allowlists and documentation links before distribution."""

import re
import argparse
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {".upstream", ".git", ".venv", ".uv-cache", "workspaces", "private", "__pycache__"}


def check_members(names):
    for name in names:
        path = Path(name)
        if any(part in FORBIDDEN for part in path.parts) or path.suffix.lower() in {".docx", ".nd2", ".tif", ".sqlite3", ".pyc"}:
            raise ValueError(f"Forbidden release member: {name}")
        if path.name.startswith(".env"):
            raise ValueError(f"Environment file in archive: {name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    directory = parser.parse_args().dist
    archives = [*directory.glob("*.whl"), *directory.glob("*.tar.gz")]
    if len(archives) != 2:
        raise ValueError("Build exactly one wheel and one source archive before the release check")
    for archive in archives:
        if archive.suffix == ".whl":
            with zipfile.ZipFile(archive) as handle:
                names = handle.namelist()
        else:
            with tarfile.open(archive) as handle:
                names = handle.getnames()
        check_members(names)
        if not any(name.endswith("scientist_os/static/index.html") for name in names):
            raise ValueError("Browser interface missing from package")
        if not any(name.endswith("LICENSE") for name in names):
            raise ValueError("License missing from package")
        print(f"Inspected {archive.name}: {len(names)} members; no forbidden paths")
    documents = [*ROOT.glob("*.md"), *ROOT.joinpath("docs").rglob("*.md")]
    for document in documents:
        for destination in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            if destination.startswith(("http:", "https:", "#", "mailto:")):
                continue
            target = destination.split("#", 1)[0].strip("<>")
            if target and not (document.parent / target).exists():
                raise ValueError(f"Broken link in {document.relative_to(ROOT)}: {destination}")
    print(f"Checked relative links in {len(documents)} Markdown documents")


if __name__ == "__main__":
    main()
