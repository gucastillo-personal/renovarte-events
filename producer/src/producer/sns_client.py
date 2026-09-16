"""Único módulo de este proyecto que llama a AWS.

Construye el mensaje SNS a partir de `price-changes.json` (ver
docs/evento-price-changes.md) y lo publica al topic.
"""

import json
from datetime import UTC, datetime
from typing import Any

import boto3

from producer.models import PriceChangesFile, ProductChange

EVENT_TYPE = "renovarte.price_changes.v1"
SOURCE = "renovarte-pipeline/publish"
MAX_CHANGES = 200  # tope defensivo: un mensaje SNS no puede pasar 256KB


def build_message(price_changes: PriceChangesFile) -> dict[str, object]:
    changes: list[ProductChange] = price_changes["changes"]
    summary: dict[str, int] = {"added": 0, "removed": 0, "price_up": 0, "price_down": 0}
    for change in changes:
        summary[change["kind"]] += 1
    summary["total"] = len(changes)
    return {
        "schema_version": 1,
        "event_type": EVENT_TYPE,
        "source": SOURCE,
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": summary,
        "changes": changes[:MAX_CHANGES],
    }


def _sns_client(region: str | None) -> Any:
    """Punto de indirección chico para poder testear `publish` sin AWS real."""
    return boto3.client("sns", region_name=region)


def publish(topic_arn: str, message: dict[str, object], region: str | None = None) -> str:
    client = _sns_client(region)
    response = client.publish(
        TopicArn=topic_arn,
        Message=json.dumps(message, ensure_ascii=False),
        MessageAttributes={
            "event_type": {"DataType": "String", "StringValue": str(message["event_type"])},
        },
    )
    return str(response["MessageId"])
