# Contrato: cambios de precio

Dos formatos distintos en dos puntos del flujo — no son el mismo objeto.

## 1. `data/price-changes.json` (renovarte-pipeline → producer)

Generado por `renovarte-pipeline` (`src/pipeline/publish/price_diff.py`) en
cada corrida de `publish`, comparando el `products.json` viejo (ya publicado
en `renovarte-catalogo`) contra el nuevo. Es un contrato de datos neutro:
`renovarte-pipeline` no sabe nada de AWS, y este repo no sabe nada de cómo
se calculó el diff. Solo lleva campos ya públicos (`id`, `nombre`,
`precio_venta`) — nunca costo ni margen.

```json
{
  "schema_version": 1,
  "generated_at": "2026-09-16T09:03:11+00:00",
  "changes": [
    { "kind": "added",      "id": "srl-1023", "nombre": "Rodillo Antigota 23cm", "old_price": null,  "new_price": 4200 },
    { "kind": "removed",    "id": "srl-0899", "nombre": "Lija al Agua 220",      "old_price": 1500,  "new_price": null },
    { "kind": "price_up",   "id": "srl-0456", "nombre": "Latex Interior 20L",    "old_price": 38000, "new_price": 41000 },
    { "kind": "price_down", "id": "srl-0777", "nombre": "Esmalte Sintético 4L",  "old_price": 15900, "new_price": 13900 }
  ]
}
```

`kind` ∈ `added | removed | price_up | price_down`. `changes: []` es válido
(corrida sin novedades) — el producer no publica nada a SNS en ese caso.

## 2. Mensaje SNS/SQS (producer → consumer)

Armado por `producer/src/producer/sns_client.py` a partir del archivo de
arriba, con un resumen agregado y un tope defensivo de 200 items (límite de
256KB de un mensaje SNS). La subscription SNS→SQS usa
`raw_message_delivery = true`, así que el body que recibe la Lambda es
exactamente este JSON, sin el sobre de SNS.

```json
{
  "schema_version": 1,
  "event_type": "renovarte.price_changes.v1",
  "source": "renovarte-pipeline/publish",
  "generated_at": "2026-09-16T09:03:20+00:00",
  "summary": { "added": 1, "removed": 1, "price_up": 1, "price_down": 1, "total": 4 },
  "changes": [ /* mismo shape que arriba, truncado a 200 */ ]
}
```

`event_type` también viaja como message attribute de SNS
(`StringValue: "renovarte.price_changes.v1"`) — no se usa hoy (un solo
consumidor) pero deja el topic listo para filter policies si mañana se suma
otro suscriptor.
