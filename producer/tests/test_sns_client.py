"""Tests de sns_client: build_message() es puro; publish() se testea con un
stub inyectado en `_sns_client` (sin mockear boto3 directo, sin dependencias
nuevas)."""

import json
from typing import Any

import pytest

from producer import sns_client
from producer.models import PriceChangesFile, ProductChange

SAMPLE: PriceChangesFile = {
    "schema_version": 1,
    "generated_at": "2026-09-16T09:03:11+00:00",
    "changes": [
        {"kind": "price_up", "id": "srl-1", "nombre": "A", "old_price": 100, "new_price": 120},
        {"kind": "added", "id": "srl-2", "nombre": "B", "old_price": None, "new_price": 50},
    ],
}


def test_build_message_summarizes_by_kind() -> None:
    message = sns_client.build_message(SAMPLE)

    assert message["event_type"] == "renovarte.price_changes.v1"
    assert message["source"] == "renovarte-pipeline/publish"
    assert message["summary"] == {"added": 1, "removed": 0, "price_up": 1, "price_down": 0, "total": 2}
    assert message["changes"] == SAMPLE["changes"]


def test_build_message_truncates_to_max_changes() -> None:
    many_changes: list[ProductChange] = [
        ProductChange(kind="added", id=f"srl-{i}", nombre=f"P{i}", old_price=None, new_price=1)
        for i in range(250)
    ]
    payload: PriceChangesFile = {"schema_version": 1, "generated_at": "x", "changes": many_changes}

    message = sns_client.build_message(payload)

    assert isinstance(message["changes"], list)
    assert len(message["changes"]) == sns_client.MAX_CHANGES
    assert isinstance(message["summary"], dict)
    assert message["summary"]["total"] == 250


class _StubSnsClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def publish(self, **kwargs: Any) -> dict[str, str]:
        self.calls.append(kwargs)
        return {"MessageId": "fake-message-id"}


def test_publish_calls_sns_with_expected_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    stub = _StubSnsClient()
    monkeypatch.setattr(sns_client, "_sns_client", lambda region: stub)

    message = sns_client.build_message(SAMPLE)
    message_id = sns_client.publish("arn:aws:sns:us-east-1:123:topic", message, region="us-east-1")

    assert message_id == "fake-message-id"
    assert len(stub.calls) == 1
    call = stub.calls[0]
    assert call["TopicArn"] == "arn:aws:sns:us-east-1:123:topic"
    assert json.loads(call["Message"]) == message
    assert call["MessageAttributes"]["event_type"]["StringValue"] == "renovarte.price_changes.v1"
