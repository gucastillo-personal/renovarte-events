"""Modelos del contrato `price-changes.json` (ver docs/evento-price-changes.md).

Sin pydantic a propósito: este paquete es chico y el contrato ya lo valida
`renovarte-pipeline` del lado que lo produce — acá alcanza con TypedDict +
un parseo defensivo mínimo antes de publicar a SNS.
"""

from typing import Literal, TypedDict

ChangeKind = Literal["added", "removed", "price_up", "price_down"]

VALID_KINDS = {"added", "removed", "price_up", "price_down"}


class ProductChange(TypedDict):
    kind: ChangeKind
    id: str
    nombre: str
    old_price: int | None
    new_price: int | None


class PriceChangesFile(TypedDict):
    schema_version: int
    generated_at: str
    changes: list[ProductChange]


def parse_price_changes(raw: object) -> PriceChangesFile:
    """Valida la forma mínima de `price-changes.json`.

    Lanza `ValueError` con un mensaje claro ante cualquier desvío del
    contrato — mejor fallar acá con un mensaje útil que publicar basura a SNS.
    """
    if not isinstance(raw, dict):
        raise ValueError(f"price-changes debe ser un objeto, no {type(raw).__name__}")
    if raw.get("schema_version") != 1:
        raise ValueError(f"schema_version no soportado: {raw.get('schema_version')!r}")
    changes = raw.get("changes")
    if not isinstance(changes, list):
        raise ValueError("price-changes.changes debe ser una lista")
    for index, change in enumerate(changes):
        if not isinstance(change, dict):
            raise ValueError(f"changes[{index}] no es un objeto: {change!r}")
        kind = change.get("kind")
        if kind not in VALID_KINDS:
            raise ValueError(f"changes[{index}].kind inválido: {kind!r}")
        for field in ("id", "nombre"):
            if not isinstance(change.get(field), str):
                raise ValueError(f"changes[{index}].{field} debe ser string")
    return raw  # type: ignore[return-value]
