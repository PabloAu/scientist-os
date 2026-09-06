"""Regressions for human review, bound figure bytes and numeric input boundaries."""

import pytest
from fastapi.testclient import TestClient

from scientist_os.app import create_app
from scientist_os.service import analyze, create_figure
from scientist_os.workspace import Workspace


def test_review_regenerate_download_preserves_exact_registered_svg(tmp_path):
    workspace = Workspace(tmp_path)
    data = workspace.create_record("dataset", "Synthetic calibration", "group,day,signal\na,A,1\na,B,3\n",
                                   metadata={"units": "arbitrary units"})
    result = analyze(workspace, {"dataset_id": data["id"], "value_column": "signal",
                                  "group_column": "group", "unit_column": "day"})
    with TestClient(create_app(tmp_path)) as client:
        response = client.get(f"/api/records/{result['output']['id']}/figure")
        assert response.text == result["output"]["content"]
        reviewed = workspace.review_record(result["analysis"]["id"], expected_revision=1,
                                             decision="approved", reviewer="Synthetic test actor")
        assert client.get(f"/api/records/{result['output']['id']}/figure").status_code == 409
        regenerated = create_figure(workspace, reviewed)
        new_response = client.get(f"/api/records/{regenerated['id']}/figure")
        assert new_response.status_code == 200
        assert new_response.text == regenerated["content"]
        assert regenerated["metadata"]["input_revisions"] == {reviewed["id"]: reviewed["revision"]}
        assert result["result"]["measurement_units"] == "arbitrary units"


@pytest.mark.parametrize("effect,independence", [("1e-999", "A"), ("1_000", "A"), ("0.2", "")])
def test_meta_parser_never_infers_or_silently_underflows_values(tmp_path, effect, independence):
    workspace = Workspace(tmp_path)
    data = workspace.create_record("dataset", "Synthetic studies",
                                    f"study_id,effect,standard_error,independence_id\nA,{effect},0.1,{independence}\nB,0.4,0.2,B\n")
    before = workspace.export_bundle()
    with pytest.raises(ValueError):
        analyze(workspace, {"dataset_id": data["id"], "method": "meta", "comparability_confirmed": True,
                            "effect_measure": "common synthetic scale"})
    after = workspace.export_bundle()
    assert before["records"] == after["records"]
    assert before["events"] == after["events"]


def test_analysis_rejects_a_changed_dataset_since_the_user_selected_it(tmp_path):
    workspace = Workspace(tmp_path)
    data = workspace.create_record("dataset", "Synthetic data", "signal\n1\n3\n")
    workspace.update_record(data["id"], expected_revision=1, content="signal\n10\n30\n")
    with pytest.raises(RuntimeError, match="Dataset changed"):
        analyze(workspace, {"dataset_id": data["id"], "expected_revision": 1, "value_column": "signal"})
    assert len(workspace.list_records()) == 1
