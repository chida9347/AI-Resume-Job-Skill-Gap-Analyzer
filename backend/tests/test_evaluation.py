"""The evaluation dataset and metrics script stay runnable and honest."""

from __future__ import annotations

import json

from evaluation.evaluate import DATASET, evaluate


def test_dataset_is_valid_and_non_trivial():
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    assert data["version"] >= 1
    assert len(data["cases"]) >= 10
    ids = [case["id"] for case in data["cases"]]
    assert len(ids) == len(set(ids))
    for case in data["cases"]:
        assert case["resume"].strip()
        assert case["job"].strip()
        assert isinstance(case["expected_required"], list)
        assert isinstance(case["expected_matched_required"], list)


def test_hybrid_matching_beats_literal_keyword_matching():
    report = evaluate(with_semantic=False)
    assert report["semantic_available"] is True  # not requested, so not skipped
    assert report["matching"]["hybrid"]["f1"] >= report["matching"]["keyword"]["f1"]
    assert report["matching"]["hybrid"]["f1"] >= 0.9
    assert report["matching"]["hybrid"]["false_positive_rate"] <= 0.1


def test_semantic_is_optional_and_never_required():
    report = evaluate(with_semantic=False)
    assert "semantic" not in report["matching"]
    assert report["semantic_requested"] is False
