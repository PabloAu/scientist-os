"""Original CC0-1.0 fictional review fixture, never a real literature corpus."""

from scientist_os.workspace import Workspace


def create_spec(workspace: Workspace) -> dict:
    """Register transparent invented reports and return the draft review payload."""
    studies, extractions = [], []
    for label, effect in (("A", 0), ("B", 2), ("C", 4)):
        study_id = "fictional-" + label
        quote = f"Fictional report {label}: effect estimate {effect}, standard error 1, independent simulation sample {label}."
        source = workspace.create_record("source", "Fictional methods exercise " + label,
                                          quote + "\nThese are deliberately invented exercise numbers, not published research.",
                                          metadata={"authority": "original fictional fixture",
                                                    "locator": "examples/pipelines/meta_fixture.py",
                                                    "license": "CC0-1.0", "synthetic": True,
                                                    "external_allowed": True})
        studies.append({"study_id": study_id, "citation": "Fictional methods exercise " + label,
                        "status": "included", "reason": "Matches the predefined arithmetic fixture",
                        "decision_actor": "Scientist OS development agent (fixture only)",
                        "selection_locator": "Original fictional source, sentence 1",
                        "independence_id": "simulation-" + label, "design": "invented independent simulation summary",
                        "population": "No population: arithmetic fixture",
                        "limitations": "Not a real study; no literature conclusion is possible",
                        "risk_of_bias": "Not assessed: fictional exercise, not substantive synthesis"})
        extractions.append({"study_id": study_id, "effect": effect, "standard_error": 1,
                            "source_id": source["id"], "source_revision": source["revision"],
                            "source_sha256": source["sha256"], "locator": "sentence 1", "quote": quote,
                            "estimand": "fictional mean difference", "scale": "mean difference",
                            "direction": "positive favors the fictional perturbation", "units": "arbitrary units",
                            "transformation": "none; known fixture numbers copied exactly",
                            "verification": {"status": "source_checked", "actor": "development agent",
                                             "method": "Direct inspection of original generated source text; no literature claim"},
                            "limitations": "Known arithmetic fixture; no real extraction reliability established"})
    studies.append({"study_id": "fictional-B-duplicate", "citation": "Fictional methods exercise B",
                    "status": "duplicate", "duplicate_of": "fictional-B", "reason": "Exact duplicate fixture report",
                    "decision_actor": "development agent (fixture only)", "selection_locator": "Exact citation identity"})
    studies.append({"study_id": "fictional-incompatible", "citation": "Fictional incompatible ratio exercise",
                    "status": "excluded", "reason": "Ratio scale differs from the predefined mean difference",
                    "decision_actor": "development agent (fixture only)", "selection_locator": "Fixture study definition"})
    return {"question": "How does the transparent calculator pool three fictional mean differences?",
            "synthetic": True,
            "protocol": {"eligibility": "Exactly the independent fictional mean-difference reports A–C; exclude ratio reports and duplicates",
                         "population": "No real population", "comparison": "Fictional perturbation versus reference",
                         "outcome": "Invented arithmetic estimate", "timing": "Not applicable",
                         "designs": "Independent simulation summaries", "estimand": "fictional mean difference",
                         "scale": "mean difference", "direction": "positive favors the fictional perturbation",
                         "units": "arbitrary units", "risk_of_bias_plan": "Retain fictional limitations; substantive study assessment not applicable",
                         "model": "random", "leave_one_out": True, "sensitivity_models": ["fixed"],
                         "sensitivity": [{"name": "Exclude high fictional estimate", "exclude_study_ids": ["fictional-C"],
                                          "rationale": "Predeclared arithmetic influence demonstration"}]},
            "search_log": [{"database": "Original local CC0 fictional fixture", "query": "All five defined exercise reports",
                            "date": "2026-09-07", "scope": "Finite fixture inventory; no web literature search",
                            "results_count": 5, "limitations": "This is not a systematic literature search"}],
            "studies": studies, "extractions": extractions,
            "comparability": {"pooling_justified": True, "rationale": "Common generated mean-difference scale by construction",
                              "independence_assessment": "Distinct invented simulation sample IDs by construction",
                              "population_comparison": "No real populations", "design_comparison": "Identical fixture definition",
                              "bias_limitations": "No biological or literature validity can follow from this fixture"}}
