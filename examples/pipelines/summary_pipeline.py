"""CC0-1.0 fictional instrument exercise; no biological observations.

Execute through Scientist OS's recorded Python runner. This file is ordinary
versioned Python, demonstrating that tools are extensible beyond a fixed menu.
"""

import argparse
import json
from pathlib import Path

from scientist_os.science import render_figure, summarize_csv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scientist-os-request", required=True)
    arguments = parser.parse_args()
    request = json.loads(Path(arguments.scientist_os_request).read_text(encoding="utf-8"))
    config = request["config"]
    output = Path(request["output_dir"])
    text = Path(request["inputs"][0]["path"]).read_text(encoding="utf-8-sig")
    result = summarize_csv(text, value_column=config["value_column"],
                           group_column=config["group_column"], unit_column=config["unit_column"])
    result["measurement_units"] = config["units"]
    result["synthetic"] = True
    result["interpretation"] = "Fictional fixed numbers demonstrate equal-weight independent-unit accounting, not a scientific effect."
    (output / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (output / "figure.svg").write_text(render_figure(result, title=config["figure_title"]), encoding="utf-8")
    minimum_units = config["minimum_independent_units"]
    checks = [{"group": group["group"], "n_units": group["n_units"],
               "minimum": minimum_units, "passed": group["n_units"] >= minimum_units}
              for group in result["groups"]]
    qc = {"passed": all(check["passed"] for check in checks), "checks": checks,
          "rows_total": result["rows_total"], "rows_excluded": result["rows_excluded"],
          "scope": "Declared unit counts only; no biological validation or independence verification."}
    (output / "qc.json").write_text(json.dumps(qc, indent=2) + "\n", encoding="utf-8")
    print(f"Summarized {result['rows_total']} fictional rows in {len(result['groups'])} groups.")


if __name__ == "__main__":
    main()
