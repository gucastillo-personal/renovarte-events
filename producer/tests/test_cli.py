import json
from pathlib import Path
from typing import Any

import pytest

from producer import cli, sns_client


def _write(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "price-changes.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_publish_command_skips_when_no_changes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _write(tmp_path, {"schema_version": 1, "generated_at": "x", "changes": []})
    args = cli.build_parser().parse_args(
        ["publish", "--input", str(path), "--topic-arn", "arn:aws:sns:x:1:t"]
    )

    exit_code = args.func(args)

    assert exit_code == 0
    assert "sin cambios" in capsys.readouterr().out


def test_publish_command_publishes_once_when_changes_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = {
        "schema_version": 1,
        "generated_at": "x",
        "changes": [{"kind": "added", "id": "srl-1", "nombre": "A", "old_price": None, "new_price": 10}],
    }
    path = _write(tmp_path, payload)

    calls: list[tuple[str, dict[str, object]]] = []

    def _fake_publish(topic_arn: str, message: dict[str, object], region: str | None = None) -> str:
        calls.append((topic_arn, message))
        return "mid"

    monkeypatch.setattr(sns_client, "publish", _fake_publish)

    args = cli.build_parser().parse_args(
        ["publish", "--input", str(path), "--topic-arn", "arn:aws:sns:x:1:t"]
    )
    exit_code = args.func(args)

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0][0] == "arn:aws:sns:x:1:t"


def test_publish_command_dry_run_does_not_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = {
        "schema_version": 1,
        "generated_at": "x",
        "changes": [{"kind": "added", "id": "srl-1", "nombre": "A", "old_price": None, "new_price": 10}],
    }
    path = _write(tmp_path, payload)

    calls: list[int] = []

    def _fake_publish(topic_arn: str, message: dict[str, object], region: str | None = None) -> str:
        calls.append(1)
        return "mid"

    monkeypatch.setattr(sns_client, "publish", _fake_publish)

    args = cli.build_parser().parse_args(
        ["publish", "--input", str(path), "--topic-arn", "arn:aws:sns:x:1:t", "--dry-run"]
    )
    exit_code = args.func(args)

    assert exit_code == 0
    assert calls == []
    assert "dry-run" in capsys.readouterr().out


def test_publish_command_fails_clearly_on_missing_topic_arn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = {
        "schema_version": 1,
        "generated_at": "x",
        "changes": [{"kind": "added", "id": "srl-1", "nombre": "A", "old_price": None, "new_price": 10}],
    }
    path = _write(tmp_path, payload)
    monkeypatch.delenv("SNS_TOPIC_ARN", raising=False)

    args = cli.build_parser().parse_args(["publish", "--input", str(path)])
    exit_code = args.func(args)

    assert exit_code == 1


def test_publish_command_fails_clearly_on_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "price-changes.json"
    path.write_text("{not json", encoding="utf-8")

    args = cli.build_parser().parse_args(
        ["publish", "--input", str(path), "--topic-arn", "arn:aws:sns:x:1:t"]
    )
    exit_code = args.func(args)

    assert exit_code == 1


def test_publish_command_fails_clearly_on_invalid_contract(tmp_path: Path) -> None:
    path = _write(tmp_path, {"schema_version": 2, "generated_at": "x", "changes": []})

    args = cli.build_parser().parse_args(
        ["publish", "--input", str(path), "--topic-arn", "arn:aws:sns:x:1:t"]
    )
    exit_code = args.func(args)

    assert exit_code == 1
