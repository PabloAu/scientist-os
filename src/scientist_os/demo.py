"""Original fictional teaching fixtures. No Cell-iSCAT data or scientific claims."""

from .workspace import Workspace


def seed_demo(workspace: Workspace, domain: str = "microscopy") -> list[dict]:
    if domain not in {"microscopy", "environment"}:
        raise ValueError("Choose microscopy or environment")
    if workspace.list_records():
        raise ValueError("Load the example into an empty workspace to avoid mixing it with research")
    biological = domain == "microscopy"
    subject = "fluorescence" if biological else "water sensor"
    records = []

    def add(kind, title, content, metadata=None, links=None):
        record = workspace.create_record(
            kind, title, content,
            metadata={"synthetic": True, "license": "CC0-1.0", "external_allowed": True,
                      **(metadata or {})}, links=links or [],
        )
        records.append(record)
        return record

    material = add("material", "Fictional calibration standard", "Teaching material; no physical sample exists.",
                   {"catalogue": "SIM-001", "lot": "fictional-A"})
    protocol = add("protocol", "Independent-day calibration protocol v1",
                   "Measure one control and one treatment preparation on three independent days per group. "
                   "Two readings within a day are technical repeats. Preserve all readings, including failures.",
                   {"protocol_version": "1.0", "independence_unit": "day"}, [material["id"]])
    source = add("source", "Example study notes · synthetic evidence",
                 "This is a fictional teaching example, not a published study.\n"
                 f"The {subject} dataset contains three independent days per group and two technical readings per day.\n"
                 "The example supports only a descriptive comparison within its synthetic generator.\n"
                 "There is no evidence here that the treatment changes cell viability or establishes causation.\n"
                 "The acquisition order was not randomized and the operator was not blinded.\n"
                 "A follow-up should randomize acquisition order, blind sample labels, and prespecify exclusions.\n",
                 {"authority": "synthetic_example", "locator": "UTF-8 teaching notes, lines 1–6"})
    add("source", "Contradictory pilot note · synthetic evidence",
        "This fictional pilot used one day only. A lower signal was observed under treatment.\n"
        "The pilot is not an independent replication of the three-day example.\n"
        "Different acquisition settings prevent pooling its raw signal measurements with the main example.\n",
        {"authority": "synthetic_example", "locator": "UTF-8 teaching notes, lines 1–3"})
    dataset = add("dataset", f"Synthetic {subject} readings",
                  "group,day,signal\ncontrol,C1,9\ncontrol,C1,11\ncontrol,C2,11\ncontrol,C2,13\n"
                  "control,C3,10\ncontrol,C3,12\ntreatment,T1,12\ntreatment,T1,14\n"
                  "treatment,T2,14\ntreatment,T2,16\ntreatment,T3,13\ntreatment,T3,15\n",
                  {"format": "csv", "units": "arbitrary units", "independence_unit": "day",
                   "exclusions": "None", "randomization": "not randomized", "blinding": "not blinded",
                   "description": "Twelve readings; six independent days, three per group."},
                  [protocol["id"], material["id"], source["id"]])
    add("dataset", "Synthetic study-level effects",
        "study_id,effect,standard_error,independence_id\nSIM-A,0.2,0.1,A\nSIM-B,0.4,0.2,B\n"
        "SIM-C,0.1,0.15,C\nSIM-D,0.5,0.25,D\n",
        {"format": "csv", "units": "hypothetical standardized effect", "independence_unit": "study",
         "effect_measure": "fictional common effect scale", "exclusions": "None"}, [source["id"]])
    add("term", "Independent experimental unit",
        "The smallest independently assigned or sampled unit that supports the intended comparison. "
        "In this example it is day; repeated readings are technical repeats.",
        {"preferred_term": "independent experimental unit", "aliases": ["unit of independence"]},
        [source["id"], dataset["id"]])
    add("claim", "Synthetic treatment signal is higher in this example",
        "A descriptive candidate claim requiring analysis and human review. No biological inference is justified.",
        {"claim_strength": "descriptive", "citations": [{"record_id": source["id"],
          "quote": "The example supports only a descriptive comparison within its synthetic generator.",
          "sha256": source["sha256"]}]}, [source["id"], dataset["id"]])
    return records
