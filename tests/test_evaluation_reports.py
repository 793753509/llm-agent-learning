"""离线回归：报告应能追到实际执行，坏用例和错误结果不能被判成通过。"""

import json
from pathlib import Path

import pytest

from day08.eval_retrieval import evaluate as evaluate_retrieval


def write_cases(path: Path, cases: list) -> Path:
    path.write_text(json.dumps(cases, ensure_ascii=False), encoding="utf-8")
    return path


def test_retrieval_report_preserves_inputs_and_actual_evidence(tmp_path):
    cases = write_cases(
        tmp_path / "cases.json",
        [
            {
                "id": "two-pieces",
                "question": "工作日和周末分别几点关门？",
                "relevant_chunk_ids": ["hours.md#1", "hours.md#2"],
            }
        ],
    )
    report = evaluate_retrieval(1, cases)
    assert report["dataset"] == str(cases)
    assert report["knowledge"] == "day05/knowledge/"
    assert report["generated_at"]
    row = report["cases"][0]
    assert row["retrieved"] == ["hours.md#2"]
    assert (row["hit"], row["recall"], row["rr"]) == (1, 0.5, 1)
    assert evaluate_retrieval(2, cases)["cases"][0]["recall"] == 1


@pytest.mark.parametrize(
    "cases",
    [
        [],
        [{"id": "empty", "question": "未知", "relevant_chunk_ids": []}],
        [
            {
                "id": "duplicate-label",
                "question": "周末",
                "relevant_chunk_ids": ["hours.md#1", "hours.md#1"],
            }
        ],
        [
            {
                "id": "missing-label",
                "question": "周末",
                "relevant_chunk_ids": ["missing"],
            }
        ],
        [{"id": "bad-type", "question": "周末", "relevant_chunk_ids": "hours.md#1"}],
        [{"id": "duplicate", "question": "周末", "relevant_chunk_ids": ["hours.md#1"]}]
        * 2,
    ],
)
def test_invalid_retrieval_dataset_is_not_scored(tmp_path, cases):
    with pytest.raises(ValueError):
        evaluate_retrieval(1, write_cases(tmp_path / "cases.json", cases))


def test_workflow_report_keeps_answer_and_faulty_trace():
    pytest.importorskip("langgraph")
    from day14.eval_agent import evaluate

    normal = evaluate()
    fault = evaluate(True)
    assert normal["passed"] == 4
    assert fault["passed"] == 0
    for good, bad in zip(normal["cases"], fault["cases"]):
        assert good["answer"] == bad["answer"] == good["expected"]
        assert good["input"] == bad["input"]
        assert any(e["node"] == "tool" for e in good["events"])
        assert all(e["node"] != "tool" for e in bad["events"])
        assert bad["checks"]["answer"] is True
        assert bad["passed"] is False


@pytest.mark.parametrize(
    "cases",
    [
        [],
        [{"id": "bool", "a": True, "b": 3, "expected": "3"}],
        [{"id": "number-answer", "a": 2, "b": 3, "expected": 6}],
        [{"id": "duplicate", "a": 2, "b": 3, "expected": "6"}] * 2,
    ],
)
def test_invalid_workflow_dataset_is_not_scored(tmp_path, cases):
    pytest.importorskip("langgraph")
    from day14.eval_agent import evaluate

    with pytest.raises(ValueError):
        evaluate(cases_path=write_cases(tmp_path / "cases.json", cases))


def test_gateway_grading_rejects_empty_success_and_leaked_error(monkeypatch):
    from day16 import gateway

    monkeypatch.setattr(gateway, "dispatch", lambda *a, **kw: {})
    assert gateway.evaluate()[0]["passed"] is False
    monkeypatch.setattr(
        gateway,
        "dispatch",
        lambda *a, **kw: {"error": "not_found_or_forbidden", "title": "private"},
    )
    assert gateway.evaluate()[1]["passed"] is False


def test_report_writer_creates_missing_directory_and_keeps_both_formats(tmp_path):
    pytest.importorskip("langgraph")
    pytest.importorskip("mcp")
    pytest.importorskip("fastapi")
    from day21.verify import write_report

    # 人工构造写文件所需的最小数据，只测试报告保存，不把它当实际验收结果。
    report = {
        "passed": 0,
        "total": 1,
        "scope": "writer test fixture",
        "generated_at": "2026-01-01T00:00:00+00:00",
        "hybrid": False,
        "python": "test",
        "checks": [{"name": "示例检查", "passed": False}],
        "latency": {"scope": "fixture", "p50": 1, "p95": 2},
    }
    destination = tmp_path / "new" / "reports"
    assert not destination.exists()
    path = write_report(report, destination)
    assert json.loads(path.read_text(encoding="utf-8")) == report
    markdown = path.with_suffix(".md").read_text(encoding="utf-8")
    assert "0/1" in markdown
    assert "| 示例检查 | 失败 |" in markdown
