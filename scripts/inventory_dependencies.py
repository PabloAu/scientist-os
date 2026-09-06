"""Record installed distribution/license metadata; no compliance certification."""

from hashlib import sha256
from importlib.metadata import distributions
from pathlib import Path
import platform
import tomllib

from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]


def main():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    direct = {Requirement(r).name.lower().replace("_", "-") for r in project["project"]["dependencies"]}
    rows = []
    for dist in sorted(distributions(), key=lambda d: d.metadata["Name"].lower()):
        meta = dist.metadata
        name = meta["Name"]
        if name.lower() == "scientist-os":
            continue
        declared = meta.get("License-Expression") or meta.get("License")
        if not declared:
            declared = "; ".join(c for c in meta.get_all("Classifier", []) if c.startswith("License ::")) or "Not declared"
        declared = declared.replace("|", "\\|").replace("\n", " ")
        if len(declared) > 190:
            declared = declared[:190] + "… (full text in distribution metadata)"
        license_files = ", ".join(meta.get_all("License-File", [])) or "Not declared in License-File metadata"
        relationship = "Direct runtime" if name.lower().replace("_", "-") in direct else "MCP/dev/transitive"
        rows.append(f"| {name} | {dist.version} | {relationship} | {declared} | {license_files} |")
    text = f"""# Dependency and license metadata inventory

Recorded from the release environment on 2026-09-06. Python {platform.python_version()}; {platform.platform()}.
Lockfile SHA-256: `{sha256((ROOT / 'uv.lock').read_bytes()).hexdigest()}`.
The installed base/MCP/development environment contains {len(rows)} third-party distributions.

Generated with `uv run python scripts/inventory_dependencies.py`. Exact installed metadata is reported;
this is not a vulnerability scan, a legal opinion or a certification of license compliance.
Other operating systems and selected extras may produce a different installed closure.
The Hatchling build backend is pinned separately in pyproject.toml; its isolated transitive build
environment is not represented by the application lockfile or this table.

Scientific summaries/meta-analysis use the Python standard library. Authoring adds python-pptx,
python-docx, pypdf, defusedxml, matplotlib and Pillow. Scientific plot export uses trusted numeric
results; imported SVG or Office code is never executed. Office applications used for local visual
verification are not product dependencies and are not bundled.

| Distribution | Version | Relationship | Declared license metadata | Declared license files |
| --- | --- | --- | --- | --- |
""" + "\n".join(rows) + """

Third-party components retain their own licenses. Apache-2.0 applies to Scientist OS generic code,
not imported papers, model weights, dependency components or research data. License classifiers
may not identify an exact SPDX variant; inspect the referenced distributions' actual license files
before redistributing a bundled installer. Preserve their original notices. No third-party skill
implementation or proprietary Office runtime is redistributed here.
"""
    (ROOT / "docs/DEPENDENCIES.md").write_text(text, encoding="utf-8")
    print(f"Recorded {len(rows)} distributions")


if __name__ == "__main__":
    main()
