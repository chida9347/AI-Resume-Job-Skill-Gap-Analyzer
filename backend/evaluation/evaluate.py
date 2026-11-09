"""Offline evaluation of skill extraction and resume-to-job matching.

Run from the backend directory::

    .\\.venv\\Scripts\\python.exe evaluation\\evaluate.py
    .\\.venv\\Scripts\\python.exe evaluation\\evaluate.py --with-semantic

The script is deliberately dependency-light: it never calls an LLM and only uses
the local semantic model when ``--with-semantic`` is passed *and* the model is
already installed. Semantic matches are reported as partial evidence, never as
proven experience.

Metrics are macro-averaged over the hand-labelled cases in ``dataset.json``:

* precision / recall / F1 for required-skill extraction from the job text
* precision / recall / F1 for resume-to-job matching
* false-positive rate (share of predicted matches that the label rejects)
* precision@3 over the ordered list of predicted matches
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.analyzer import compare_resume_to_job  # noqa: E402
from services.job_service import analyze_job_description  # noqa: E402
from services.resume_structurer import extract_structured_resume  # noqa: E402
from services.skill_taxonomy import DISPLAY_NAMES, extract_canonical_skills  # noqa: E402

DATASET = Path(__file__).with_name("dataset.json")


def _prf(predicted: list[str], expected: list[str]) -> tuple[float, float, float]:
    predicted_set = set(predicted)
    expected_set = set(expected)
    true_positive = len(predicted_set & expected_set)
    if predicted_set:
        precision = true_positive / len(predicted_set)
    else:
        precision = 1.0 if not expected_set else 0.0
    if expected_set:
        recall = true_positive / len(expected_set)
    else:
        recall = 1.0 if not predicted_set else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def _keyword_present(skill: str, resume: str) -> bool:
    display = DISPLAY_NAMES.get(skill, skill)
    pattern = r"(?<![A-Za-z0-9])" + re.escape(display) + r"(?![A-Za-z0-9])"
    return re.search(pattern, resume, re.IGNORECASE) is not None


def _keyword_matches(required: list[str], resume: str) -> list[str]:
    """Literal keyword matching only: no synonyms, no implications."""
    return [skill for skill in required if _keyword_present(skill, resume)]


def _synonym_matches(required: list[str], resume: str) -> list[str]:
    """Taxonomy alias matching without implication or semantic similarity."""
    resume_set = set(extract_canonical_skills(resume))
    return [skill for skill in required if skill in resume_set]


def _hybrid_matches(resume: str, required: list[str]) -> tuple[list[str], list[str]]:
    structured = extract_structured_resume(resume)
    comparison = compare_resume_to_job(
        resume,
        structured["skills"]["all"],
        required,
        [],
        resume_confidence=structured["confidence"],
    )
    return comparison["matched_required"], comparison["partial_required"]


def _semantic_matches(required: list[str], resume: str) -> list[str] | None:
    """Optional semantic layer. Returns None when no local model is available."""
    try:
        from services.analyzer import _semantic_scores

        resume_set = set(extract_canonical_skills(resume))
        missing = [skill for skill in required if skill not in resume_set]
        scores = _semantic_scores(missing, resume_set)
    except Exception:
        return None
    if not scores and missing:
        return None
    return [*[skill for skill in required if skill in resume_set], *scores]


def _precision_at_k(predicted: list[str], expected: list[str], k: int = 3) -> float:
    top = predicted[:k]
    if not top:
        return 1.0 if not expected else 0.0
    return len(set(top) & set(expected)) / len(top)


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 3) if values else 0.0


def evaluate(with_semantic: bool = False) -> dict:
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    cases = data["cases"]
    methods = ["keyword", "synonym", "hybrid"] + (["semantic"] if with_semantic else [])
    results: dict[str, list[dict]] = {method: [] for method in methods}
    extraction_rows: list[dict] = []
    semantic_available = True

    for case in cases:
        resume = case["resume"]
        required = case["expected_required"]
        expected = case["expected_matched_required"]

        job_intel = analyze_job_description(case["job"])
        predicted_required = job_intel["required_skills"]
        extraction_rows.append(
            {
                "id": case["id"],
                "expected": required,
                "predicted": predicted_required,
                "precision": _prf(predicted_required, required)[0],
                "recall": _prf(predicted_required, required)[1],
                "f1": _prf(predicted_required, required)[2],
            }
        )

        predictions: dict[str, list[str] | None] = {
            "keyword": _keyword_matches(required, resume),
            "synonym": _synonym_matches(required, resume),
        }
        hybrid_matched, hybrid_partial = _hybrid_matches(resume, required)
        predictions["hybrid"] = hybrid_matched
        if with_semantic:
            semantic = _semantic_matches(required, resume)
            if semantic is None:
                semantic_available = False
            predictions["semantic"] = semantic

        for method in methods:
            predicted = predictions.get(method)
            if predicted is None:
                results[method].append({"id": case["id"], "skipped": True})
                continue
            precision, recall, f1 = _prf(predicted, expected)
            false_positives = len(set(predicted) - set(expected))
            results[method].append(
                {
                    "id": case["id"],
                    "predicted": predicted,
                    "expected": expected,
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                    "false_positive_rate": false_positives / len(predicted) if predicted else 0.0,
                    "precision_at_3": _precision_at_k(predicted, expected),
                    "partial": hybrid_partial if method == "hybrid" else [],
                }
            )

    summary = {}
    for method in methods:
        rows = [row for row in results[method] if not row.get("skipped")]
        summary[method] = {
            "cases": len(rows),
            "precision": _mean([row["precision"] for row in rows]),
            "recall": _mean([row["recall"] for row in rows]),
            "f1": _mean([row["f1"] for row in rows]),
            "false_positive_rate": _mean([row["false_positive_rate"] for row in rows]),
            "precision_at_3": _mean([row["precision_at_3"] for row in rows]),
        }

    extraction_summary = {
        "cases": len(extraction_rows),
        "precision": _mean([row["precision"] for row in extraction_rows]),
        "recall": _mean([row["recall"] for row in extraction_rows]),
        "f1": _mean([row["f1"] for row in extraction_rows]),
    }

    return {
        "dataset_version": data["version"],
        "cases": len(cases),
        "semantic_requested": with_semantic,
        "semantic_available": semantic_available,
        "required_skill_extraction": extraction_summary,
        "matching": summary,
        "per_case": results,
        "notes": [
            "Semantic matches are partial evidence and are never counted as proven experience.",
            "Keyword matching is literal and cannot handle synonyms.",
            "Hybrid matching combines exact, synonym, implication and evidence layers.",
            "The dataset is small and hand-labelled; treat the numbers as a sanity check, not a benchmark.",
        ],
    }


def _print_report(report: dict) -> None:
    print(f"Dataset v{report['dataset_version']} — {report['cases']} cases")
    print()
    extraction = report["required_skill_extraction"]
    print("Required-skill extraction from job text")
    print(f"  precision={extraction['precision']:.3f} recall={extraction['recall']:.3f} f1={extraction['f1']:.3f}")
    print()
    print("Resume-to-job matching")
    print(f"  {'method':<10} {'precision':>9} {'recall':>7} {'f1':>6} {'FP rate':>8} {'P@3':>6}")
    for method, row in report["matching"].items():
        print(
            f"  {method:<10} {row['precision']:>9.3f} {row['recall']:>7.3f} "
            f"{row['f1']:>6.3f} {row['false_positive_rate']:>8.3f} {row['precision_at_3']:>6.3f}"
        )
    if report["semantic_requested"] and not report["semantic_available"]:
        print("  (semantic requested but no local model was available; semantic row is skipped)")
    print()
    print("Per-case hybrid results")
    for row in report["per_case"]["hybrid"]:
        partial = f" partial={row['partial']}" if row["partial"] else ""
        print(f"  {row['id']:<36} predicted={row['predicted']} expected={row['expected']}{partial}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-semantic", action="store_true", help="Include the optional local semantic layer.")
    parser.add_argument("--json", action="store_true", help="Print the full JSON report instead of a table.")
    parser.add_argument("--min-f1", type=float, default=0.0, help="Exit non-zero if hybrid F1 is below this value.")
    args = parser.parse_args()

    report = evaluate(with_semantic=args.with_semantic)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_report(report)

    hybrid_f1 = report["matching"]["hybrid"]["f1"]
    if hybrid_f1 < args.min_f1:
        print(f"\nHybrid F1 {hybrid_f1:.3f} is below the required {args.min_f1:.3f}.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
