# Dependency and license metadata inventory

Recorded from the release environment on 2026-09-06. Python 3.12.0; Windows-11-10.0.26200-SP0.
Lockfile SHA-256: `74b4b0f1268234acb7f121463c2364d18538cd53bdce7cbcaba6ec8a062ed221`.
The installed base/MCP/development environment contains 55 third-party distributions.

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
| annotated-doc | 0.0.5 | MCP/dev/transitive | MIT | LICENSE |
| annotated-types | 0.8.0 | MCP/dev/transitive | MIT | LICENSE |
| anyio | 4.15.1 | MCP/dev/transitive | MIT | LICENSE |
| attrs | 26.1.0 | MCP/dev/transitive | MIT | LICENSE |
| certifi | 2026.7.22 | MCP/dev/transitive | MPL-2.0 | LICENSE |
| cffi | 2.1.1 | MCP/dev/transitive | MIT-0 | LICENSE |
| click | 8.5.0 | MCP/dev/transitive | BSD-3-Clause | LICENSE.txt |
| colorama | 0.4.6 | MCP/dev/transitive | License :: OSI Approved :: BSD License | LICENSE.txt |
| contourpy | 1.3.3 | MCP/dev/transitive | BSD 3-Clause License   Copyright (c) 2021-2025, ContourPy Developers.  All rights reserved.   Redistribution and use in source and binary forms, with or without  modification, are permitted … (full text in distribution metadata) | Not declared in License-File metadata |
| cryptography | 50.0.1 | MCP/dev/transitive | Apache-2.0 OR BSD-3-Clause | LICENSE, LICENSE.APACHE, LICENSE.BSD |
| cycler | 0.12.1 | MCP/dev/transitive | Copyright (c) 2015, matplotlib project All rights reserved.  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following condit… (full text in distribution metadata) | LICENSE |
| defusedxml | 0.7.1 | Direct runtime | PSFL | Not declared in License-File metadata |
| fastapi | 0.141.1 | Direct runtime | MIT | LICENSE |
| fonttools | 4.64.0 | MCP/dev/transitive | MIT | LICENSE, LICENSE.external |
| h11 | 0.16.0 | MCP/dev/transitive | MIT | LICENSE.txt |
| httpcore | 1.0.9 | MCP/dev/transitive | BSD-3-Clause | LICENSE.md |
| httpx | 0.28.1 | Direct runtime | BSD-3-Clause | Not declared in License-File metadata |
| httpx-sse | 0.4.3 | MCP/dev/transitive | MIT | LICENSE |
| idna | 3.19 | MCP/dev/transitive | BSD-3-Clause | LICENSE.md |
| iniconfig | 2.3.0 | MCP/dev/transitive | MIT | LICENSE |
| jsonschema | 4.26.0 | MCP/dev/transitive | MIT | COPYING |
| jsonschema-specifications | 2025.9.1 | MCP/dev/transitive | MIT | COPYING |
| kiwisolver | 1.5.1 | MCP/dev/transitive | =========================  The Kiwi licensing terms ========================= Kiwi is licensed under the terms of the Modified BSD License (also known as New or Revised BSD), as follows:  Co… (full text in distribution metadata) | LICENSE |
| lxml | 6.1.3 | MCP/dev/transitive | BSD-3-Clause | LICENSE.txt, LICENSES.txt |
| matplotlib | 3.11.1 | Direct runtime | License agreement for matplotlib versions 1.3.0 and later  =========================================================   1. This LICENSE AGREEMENT is between the Matplotlib Development Team  (… (full text in distribution metadata) | Not declared in License-File metadata |
| mcp | 1.29.1 | MCP/dev/transitive | MIT | LICENSE |
| numpy | 2.5.2 | MCP/dev/transitive | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | LICENSE.txt, numpy/_core/include/numpy/libdivide/LICENSE.txt, numpy/_core/src/common/pythoncapi-compat/COPYING, numpy/_core/src/highway/LICENSE, numpy/_core/src/multiarray/dragon4_LICENSE.txt, numpy/_core/src/npysort/x86-simd-sort/LICENSE.md, numpy/_core/src/umath/svml/LICENSE, numpy/fft/pocketfft/LICENSE.md, numpy/linalg/lapack_lite/LICENSE.txt, numpy/ma/LICENSE, numpy/random/LICENSE.md, numpy/random/src/distributions/LICENSE.md, numpy/random/src/mt19937/LICENSE.md, numpy/random/src/pcg64/LICENSE.md, numpy/random/src/philox/LICENSE.md, numpy/random/src/sfc64/LICENSE.md, numpy/random/src/splitmix64/LICENSE.md |
| packaging | 26.3 | MCP/dev/transitive | Apache-2.0 OR BSD-2-Clause | LICENSE, LICENSE.APACHE, LICENSE.BSD |
| pillow | 12.3.0 | Direct runtime | MIT-CMU | LICENSE |
| pluggy | 1.6.0 | MCP/dev/transitive | MIT | LICENSE |
| pycparser | 3.0 | MCP/dev/transitive | BSD-3-Clause | LICENSE |
| pydantic | 2.13.5 | Direct runtime | MIT | LICENSE |
| pydantic-settings | 2.15.0 | MCP/dev/transitive | MIT | LICENSE |
| pydantic_core | 2.46.5 | MCP/dev/transitive | MIT | LICENSE |
| Pygments | 2.21.0 | MCP/dev/transitive | BSD-2-Clause | AUTHORS, LICENSE |
| PyJWT | 2.13.0 | MCP/dev/transitive | MIT | LICENSE, AUTHORS.rst |
| pyparsing | 3.3.2 | MCP/dev/transitive | MIT | LICENSE |
| pypdf | 6.17.0 | Direct runtime | BSD-3-Clause | LICENSE |
| pytest | 9.1.1 | MCP/dev/transitive | MIT | LICENSE |
| python-dateutil | 2.9.0.post0 | MCP/dev/transitive | Dual License | LICENSE |
| python-docx | 1.2.0 | Direct runtime | MIT | LICENSE |
| python-dotenv | 1.2.3 | MCP/dev/transitive | BSD-3-Clause | LICENSE |
| python-multipart | 0.0.32 | MCP/dev/transitive | Apache-2.0 | LICENSE.txt |
| python-pptx | 1.0.2 | Direct runtime | MIT | LICENSE |
| pywin32 | 312 | MCP/dev/transitive | PSF | adodbapi/license.txt, com/License.txt, pythonwin/License.txt, pythonwin/Scintilla/License.txt, pythonwin/pywin/idle/LICENSE.txt, win32/License.txt, com/win32comext/mapi/src/MAPIStubLibrary/LICENSE, isapi/README.txt |
| referencing | 0.37.0 | MCP/dev/transitive | MIT | COPYING |
| rpds-py | 2026.6.3 | MCP/dev/transitive | MIT | LICENSE |
| ruff | 0.16.6 | MCP/dev/transitive | MIT | LICENSE |
| six | 1.17.0 | MCP/dev/transitive | MIT | LICENSE |
| sse-starlette | 3.4.11 | MCP/dev/transitive | BSD-3-Clause | LICENSE, AUTHORS |
| starlette | 1.6.0 | MCP/dev/transitive | BSD-3-Clause | LICENSE.md |
| typing-inspection | 0.4.4 | MCP/dev/transitive | MIT | LICENSE |
| typing_extensions | 4.16.0 | MCP/dev/transitive | PSF-2.0 | LICENSE |
| uvicorn | 0.52.4 | Direct runtime | BSD-3-Clause | LICENSE.md |
| xlsxwriter | 3.2.9 | MCP/dev/transitive | BSD-2-Clause | LICENSE.txt |

Third-party components retain their own licenses. Apache-2.0 applies to Scientist OS generic code,
not imported papers, model weights, dependency components or research data. License classifiers
may not identify an exact SPDX variant; inspect the referenced distributions' actual license files
before redistributing a bundled installer. Preserve their original notices. No third-party skill
implementation or proprietary Office runtime is redistributed here.
