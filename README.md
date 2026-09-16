# renovarte-events

POC de arquitectura event-driven para el proyecto RenovArte. Objetivo:
aprender arquitectura backend / AWS / Node.js sumando algo útil al catálogo
— una notificación a Discord cuando `renovarte-pipeline` detecta cambios de
precio en el catálogo publicado.

Costo real: **$0**. Todos los recursos de AWS usados (SNS, SQS, Lambda)
están dentro del "Always Free tier" permanente al volumen de este proyecto
(corridas semanales). Ver `docs/runbook.md` para la única salvedad
(CloudWatch Logs).

## Flujo

```
renovarte-pipeline (Python)
  publish.yml calcula el diff de products.json
  → escribe data/price-changes.json (contrato neutro, sin AWS)
        │
        ▼
renovarte-events/producer (Python + boto3)   ← único lugar con credenciales AWS
  lee price-changes.json, arma el evento, SNS.publish()
        │
        ▼
   AWS SNS topic "price-changes"
        │  (subscription raw)
        ▼
   AWS SQS queue "price-changes" ──(5 reintentos fallidos)──▶ SQS DLQ
        │
        ▼
renovarte-events/consumer (Lambda, Node.js)
  procesa el batch, arma el mensaje, POST a un webhook de Discord
        │
        ▼
      Discord: "3 productos bajaron de precio, 1 nuevo..."
```

`renovarte-pipeline` nunca importa `boto3` ni conoce AWS — solo produce
`data/price-changes.json` (ver contrato en `docs/evento-price-changes.md`).
Este repo es el único dueño de la parte AWS/event-driven.

## Estructura

- `producer/` — Python (`uv`). CLI que lee `price-changes.json` y publica a
  SNS. Único lugar con `boto3`.
- `consumer/` — Node.js. Handler de Lambda que consume la SQS y notifica a
  Discord. Sin dependencias npm (usa el `fetch` nativo de Node 20 en Lambda).
- `infra/` — Terraform: SNS, SQS + DLQ, IAM (least-privilege), Lambda +
  event source mapping.
- `docs/` — contrato de datos y runbook operativo.

## Desarrollo local

Producer:
```bash
cd producer
uv sync
uv run pytest
uv run renovarte-events-producer publish --input ../fixtures/example-price-changes.json --dry-run
```

Consumer:
```bash
cd consumer
node --test test/
```

Infra (requiere Terraform instalado y credenciales AWS configuradas):
```bash
cd infra
terraform fmt -check
terraform validate
terraform plan -var-file=terraform.tfvars   # terraform.tfvars es local, gitignoreado
```

`terraform apply` y `terraform destroy` crean/destruyen recursos reales en
AWS — nunca se corren sin aprobación humana explícita en el momento (ver
`CLAUDE.md`).
