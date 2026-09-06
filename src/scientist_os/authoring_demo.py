"""An original fictional authoring example, never an unpublished research import."""

from .demo import seed_demo
from .publishing import create_presentation, import_document
from .service import analyze
from .studio import create_discussion, create_manuscript, create_reference


def seed_authoring_demo(workspace):
    if workspace.list_records():
        raise ValueError("Load the writing example into an empty workspace")
    with workspace.transaction():
        records = seed_demo(workspace)
        source = next(r for r in records if r["kind"] == "source")
        dataset = next(r for r in records if r["kind"] == "dataset")
        calculation = analyze(workspace, {"dataset_id": dataset["id"], "expected_revision": 1,
                                         "method": "summary", "value_column": "signal",
                                         "group_column": "group", "unit_column": "day"})
        figure = calculation["output"]
        reference = create_reference(workspace, title="Fictional calibration notes — teaching reference",
                                     abstract="This is an original fictional example, not a published paper. "
                                     "Only a descriptive comparison within the synthetic generator is supported.",
                                     full_text_ids=[source["id"]], external_allowed=True)
        create_manuscript(workspace, title="Independent-day calibration: a teaching manuscript",
                          external_allowed=True, sections=[
            {"title": "Abstract", "text": "We illustrate a traceable descriptive analysis using a fictional calibration experiment. The example contains three independent days per group, each with two technical readings. Group means are 11 and 14 arbitrary units. These simulated measurements do not establish a biological effect.", "reference_ids": [reference["id"]]},
            {"title": "Introduction", "text": "Repeated measurements can increase apparent sample size without adding independent evidence. This teaching example keeps technical repeats nested within days and separates observed values from scientific interpretation."},
            {"title": "Methods", "text": "Two technical readings were averaged within each day. Each group contains three independent days. All twelve readings were retained. The acquisition order was not randomized and sample labels were not blinded. No real sample was measured.", "reference_ids": [reference["id"]]},
            {"title": "Results", "text": "The control group mean was 11 arbitrary units and the treatment group mean was 14 arbitrary units. Each summary represents three independent day-level means. The standard error is approximately 0.577 arbitrary units in each group. These values describe only the declared fictional generator.", "figure_ids": [figure["id"]]},
            {"title": "Discussion", "text": "The difference between group means is descriptive. It does not establish causation, viability, or an effect in biological specimens. A future real experiment would need a prespecified hypothesis, independent preparations, randomized acquisition order, blinded labels, and an analysis suited to its sampling hierarchy."},
            {"title": "Supplementary methods", "text": "All inputs are fictional CC0 teaching fixtures. Dataset, protocol, source, analysis, and figure records retain their identifiers and revision links in the workspace. Original real research is not included.", "supplementary": True},
        ])
        create_presentation(workspace, title="Calibration study · research meeting", source_ids=[source["id"]], slides=[
            {"title": "From measurements to evidence", "body": "Independent-day calibration\nFictional teaching study", "layout": "title", "notes": "This is a demonstration of the authoring workflow. No biological experiment was performed."},
            {"title": "Preserve the experimental hierarchy", "body": "Three independent days per group\nTwo technical readings per day\nAverage readings within each day\nRetain all observations and limitations", "layout": "two_column", "reference_ids": [reference["id"]]},
            {"title": "A descriptive difference in the example", "body": "Control: 11 arbitrary units\nTreatment: 14 arbitrary units\nn = 3 independent days per group", "layout": "evidence", "figure_id": figure["id"], "notes": "Error bars show standard errors of independent day-level means. This is a synthetic example, not biological validation."},
            {"title": "What would change our interpretation?", "body": "Randomize acquisition order\nBlind sample labels\nPrespecify exclusions and the primary comparison\nUse independent biological preparations", "layout": "two_column", "notes": "Discuss these as proposed controls. They were not performed in the fictional dataset."},
        ])
        create_discussion(workspace, title="Next experiments and alternative explanations",
                          focus="Discuss what evidence a real calibration study would require. Separate observations, hypotheses, limitations, and proposed experiments.", external_allowed=True)
        import_document(workspace, filename="fictional-meeting-notes.md", category="document",
                        title="Research meeting · fictional planning notes",
                        data=b"# Fictional planning meeting\n\nNo real experiment was conducted.\n\nWe want to distinguish drift from a treatment-associated signal. Consider randomized acquisition order, blinded labels, independent preparations and prespecified exclusions. These are ideas for discussion, not validated protocols.\n")
    return workspace.list_records()
