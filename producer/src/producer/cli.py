"""CLI: `renovarte-events-producer publish --input <price-changes.json>`.

`renovarte-pipeline` corre esto como paso best-effort/no bloqueante en CI —
acá adentro sí falla ruidoso: si algo está mal, tiene que verse en los logs
del step, no tragarse en silencio.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from producer import sns_client
from producer.models import parse_price_changes


def _publish_command(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    try:
        raw = json.loads(input_path.read_text(encoding="utf-8"))
    except OSError as error:
        print(f"no pude leer {input_path}: {error}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as error:
        print(f"{input_path} no es JSON válido: {error}", file=sys.stderr)
        return 1

    try:
        price_changes = parse_price_changes(raw)
    except ValueError as error:
        print(f"price-changes inválido: {error}", file=sys.stderr)
        return 1

    if not price_changes["changes"]:
        print("sin cambios de precio — no se publica nada a SNS.")
        return 0

    topic_arn = args.topic_arn or os.environ.get("SNS_TOPIC_ARN")
    if not topic_arn:
        print("falta --topic-arn (o la env var SNS_TOPIC_ARN)", file=sys.stderr)
        return 1

    message = sns_client.build_message(price_changes)
    total = len(price_changes["changes"])

    if args.dry_run:
        print(json.dumps(message, indent=2, ensure_ascii=False))
        print(f"[dry-run] no se publicó a SNS ({total} cambio(s))")
        return 0

    region = args.region or os.environ.get("AWS_REGION")
    message_id = sns_client.publish(topic_arn, message, region=region)
    print(f"publicado a SNS ({total} cambio(s)) — MessageId {message_id}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="renovarte-events-producer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    publish_parser = subparsers.add_parser("publish", help="publica price-changes.json a SNS")
    publish_parser.add_argument("--input", required=True, help="path a price-changes.json")
    publish_parser.add_argument("--topic-arn", default=None, help="ARN del topic SNS (o env SNS_TOPIC_ARN)")
    publish_parser.add_argument("--region", default=None, help="región AWS (o env AWS_REGION)")
    publish_parser.add_argument("--dry-run", action="store_true", help="arma el mensaje pero no publica")
    publish_parser.set_defaults(func=_publish_command)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
