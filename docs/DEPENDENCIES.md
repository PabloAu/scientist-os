# Dependency and license metadata inventory

Inspection date: 6 September 2026. This file records installed distribution metadata, not guessed licenses or a certification of license compliance. The snapshot was read using `uv run --no-sync python` and `importlib.metadata` from the project environment. No dependency installation or broad test run was performed for this inventory.

Environment: **Python 3.12.0**, **Windows-11-10.0.26200-SP0**. Lockfile SHA-256: `6bb3894956d3724b5a49da666327d529df36ddae063aad2a25bf8535454f6eb6`. The tables cover **39 third-party distributions** installed for the base application, optional MCP feature and development group. Other operating systems or selected extras can produce a different installed closure.

## How the scope was determined

Direct requirements come from `pyproject.toml`: base application dependencies, the `mcp` extra, and the `dev` dependency group. Transitive requirements were traversed using each installed distribution's `Requires-Dist` metadata, evaluating environment markers for this Python/Windows environment and propagating requested extras. Shared dependencies appear once in the earliest applicable table: mandatory runtime first, then additional MCP, then additional development. All traversed active requirements were installed; no additional unclassified third-party distributions were found.

License reporting prefers the exact `License-Expression` field, then the legacy `License` field, then license classifiers. A classifier saying BSD does not establish which BSD variant applies. An absent `License-File` field is reported as absent; it does not establish that the wheel lacks a license file. The file paths below are the package's declared `License-File` metadata, not a content-by-content legal review of those files.

## Mandatory application dependencies

The four direct dependencies are FastAPI, Uvicorn, HTTPX and Pydantic. The deterministic scientific calculations use the Python standard library and add no numerical-library dependency.

| Installed distribution | Version | Relationship | Declared license metadata | Declared license files |
| --- | --- | --- | --- | --- |
| annotated-doc | 0.0.5 | Transitive | `MIT` (License-Expression) | `LICENSE` |
| annotated-types | 0.8.0 | Transitive | `MIT` (License-Expression) | `LICENSE` |
| anyio | 4.15.1 | Transitive | `MIT` (License-Expression) | `LICENSE` |
| certifi | 2026.7.22 | Transitive | `MPL-2.0` (License field) | `LICENSE` |
| click | 8.5.0 | Transitive | `BSD-3-Clause` (License-Expression) | `LICENSE.txt` |
| fastapi | 0.141.1 | Direct | `MIT` (License-Expression) | `LICENSE` |
| h11 | 0.16.0 | Transitive | `MIT` (License field) | `LICENSE.txt` |
| httpcore | 1.0.9 | Transitive | `BSD-3-Clause` (License-Expression) | `LICENSE.md` |
| httpx | 0.28.1 | Direct | `BSD-3-Clause` (License field) | Not declared in License-File metadata |
| idna | 3.19 | Transitive | `BSD-3-Clause` (License-Expression) | `LICENSE.md` |
| pydantic | 2.13.5 | Direct | `MIT` (License-Expression) | `LICENSE` |
| pydantic_core | 2.46.5 | Transitive | `MIT` (License-Expression) | `LICENSE` |
| starlette | 1.6.0 | Transitive | `BSD-3-Clause` (License-Expression) | `LICENSE.md` |
| typing_extensions | 4.16.0 | Transitive | `PSF-2.0` (License-Expression) | `LICENSE` |
| typing-inspection | 0.4.4 | Transitive | `MIT` (License-Expression) | `LICENSE` |
| uvicorn | 0.52.4 | Direct | `BSD-3-Clause` (License-Expression) | `LICENSE.md` |

## Additional dependencies for the optional MCP feature

Install the MCP extra only when using the stdio bridge. These additional distributions are not required by the base application metadata. Some platform-specific dependencies, particularly `pywin32`, apply to this Windows environment. Shared HTTP/data-validation dependencies are already listed above.

| Installed distribution | Version | Relationship | Declared license metadata | Declared license files |
| --- | --- | --- | --- | --- |
| attrs | 26.1.0 | Transitive | `MIT` (License-Expression) | `LICENSE` |
| cffi | 2.1.1 | Transitive | `MIT-0` (License-Expression) | `LICENSE` |
| cryptography | 50.0.1 | Transitive | `Apache-2.0 OR BSD-3-Clause` (License-Expression) | `LICENSE`, `LICENSE.APACHE`, `LICENSE.BSD` |
| httpx-sse | 0.4.3 | Transitive | `MIT` (License field) | `LICENSE` |
| jsonschema | 4.26.0 | Transitive | `MIT` (License-Expression) | `COPYING` |
| jsonschema-specifications | 2025.9.1 | Transitive | `MIT` (License-Expression) | `COPYING` |
| mcp | 1.29.1 | Direct | `MIT` (License field) | `LICENSE` |
| pycparser | 3.0 | Transitive | `BSD-3-Clause` (License-Expression) | `LICENSE` |
| pydantic-settings | 2.15.0 | Transitive | `MIT` (License-Expression) | `LICENSE` |
| PyJWT | 2.13.0 | Transitive | `MIT` (License-Expression) | `LICENSE`, `AUTHORS.rst` |
| python-dotenv | 1.2.3 | Transitive | `BSD-3-Clause` (License field) | `LICENSE` |
| python-multipart | 0.0.32 | Transitive | `Apache-2.0` (License-Expression) | `LICENSE.txt` |
| pywin32 | 312 | Transitive | `PSF` (License field) | `adodbapi/license.txt`, `com/License.txt`, `pythonwin/License.txt`, `pythonwin/Scintilla/License.txt`, `pythonwin/pywin/idle/LICENSE.txt`, `win32/License.txt`, `com/win32comext/mapi/src/MAPIStubLibrary/LICENSE`, `isapi/README.txt` |
| referencing | 0.37.0 | Transitive | `MIT` (License-Expression) | `COPYING` |
| rpds-py | 2026.6.3 | Transitive | `MIT` (License-Expression) | `LICENSE` |
| sse-starlette | 3.4.11 | Transitive | `BSD-3-Clause` (License-Expression) | `LICENSE`, `AUTHORS` |

## Additional development dependencies

Pytest and Ruff are direct development tools. This table excludes runtime/MCP dependencies that also happen to support development. These tools are not application runtime requirements.

| Installed distribution | Version | Relationship | Declared license metadata | Declared license files |
| --- | --- | --- | --- | --- |
| colorama | 0.4.6 | Transitive | License :: OSI Approved :: BSD License (classifier only; exact SPDX variant unspecified) | `LICENSE.txt` |
| iniconfig | 2.3.0 | Transitive | `MIT` (License-Expression) | `LICENSE` |
| packaging | 26.3 | Transitive | `Apache-2.0 OR BSD-2-Clause` (License-Expression) | `LICENSE`, `LICENSE.APACHE`, `LICENSE.BSD` |
| pluggy | 1.6.0 | Transitive | `MIT` (License field) | `LICENSE` |
| Pygments | 2.21.0 | Transitive | `BSD-2-Clause` (License-Expression) | `AUTHORS`, `LICENSE` |
| pytest | 9.1.1 | Direct | `MIT` (License-Expression) | `LICENSE` |
| ruff | 0.16.6 | Direct | `MIT` (License-Expression) | `LICENSE` |

## Product and build environment

| Item | Verified state | Scope/remaining check |
| --- | --- | --- |
| Installed editable `scientist-os` | 0.1.0b1; `License-Expression: Apache-2.0`; declared `License-File` entries `LICENSE`, `NOTICE` | Rechecked with `importlib.metadata` after the lead rebuilt/reinstalled the package. Inspect the exact release wheel/source archive as a separate packaging check. |
| Build backend | `hatchling==1.32.0`, backend `hatchling.build`, declared in `pyproject.toml` | Cached `hatchling-1.32.0.dist-info/METADATA` was inspected directly: `License-Expression: MIT`, `License-File: LICENSE.txt`. This is the pinned isolated build backend, not a runtime dependency. |
| Python interpreter | 3.12.0 | Interpreter and bundled operating-system/native libraries are outside the distribution metadata inventory. |
| Installer/environment tooling | Commands use `uv`; environment pins are in `uv.lock` | This table does not audit the uv executable, operating system, browser, inference server, external model weights or an MCP host. |

Hatchling 1.32.0 declares build dependencies `packaging>=24.2`, `pathspec>=0.10.1`, `pluggy>=1.0.0`, `tomlkit>=0.11.1`, `trove-classifiers`, and `tomli>=1.2.2` only for Python below 3.11. The exact resolved versions/licenses of its **isolated-build transitive environment are not inventoried here**. A cached backend plus an exact backend pin does not prove that every build dependency is fixed. Record that isolated environment separately for a fully specified build claim.

## Release and redistribution scope

Third-party components retain their original licenses and attribution requirements. Scientist OS's Apache-2.0 license does not relicense them, downloaded model weights, imported papers or research data. Do not replace upstream license notices with the product license. Preserve notices in dependency distributions and inspect bundled contents if creating a self-contained executable or installer.

The observed metadata includes `MPL-2.0`, `MIT-0`, BSD/PSF variants and dual-license expressions in addition to MIT/Apache declarations; this inventory does not flatten those distinctions into one blanket license. `colorama` supplies a generic BSD classifier rather than an exact SPDX expression; its actual license text needs inspection when assessing redistribution requirements. `pywin32` declares multiple component license files, which likewise merit file-level review for a bundled release.

This was a metadata audit of the installed environment. It did not conduct a vulnerability scan, resolve all legal obligations, inspect every transitive source file, verify native binary provenance or certify a future installer. Review the exact built wheel/source archive, dependency licenses and release file allowlist separately. The private upstream clone, local research workspaces, raw scientific assets and credentials must remain outside distribution.

## Refresh this inventory

After changing the lockfile, Python version, operating system or extras, recreate the intended environment, enumerate `importlib.metadata.distributions()`, and traverse active `Requires-Dist` entries again. Capture `Name`, `Version`, `License-Expression`, `License`, license classifiers and `License-File`. Compare the installed closure with the selected root requirements; explicitly report missing, unknown and unexpected packages. Record the new lockfile hash and retain the prior release's inventory rather than silently updating its historical claim.

Package metadata is evidence supplied by each distribution. Where it is incomplete or ambiguous, retain that uncertainty and inspect the original license materials before making a redistribution decision.
