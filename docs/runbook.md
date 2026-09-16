# Runbook

## Costo

Al volumen de este proyecto (corridas semanales, unos pocos mensajes por
corrida), SNS, SQS y Lambda están cubiertos por el **Always Free tier**
permanente de AWS (no el trial de 12 meses):

- SNS: 1.000.000 publish/mes gratis siempre.
- SQS: 1.000.000 requests/mes gratis siempre.
- Lambda: 1.000.000 invocaciones + 400.000 GB-s de cómputo/mes gratis siempre.

**Única salvedad:** CloudWatch Logs tiene free tier solo durante los
primeros 12 meses de la cuenta. Pasado ese período, el costo de loguear
unas pocas líneas por semana es de fracciones de centavo — no relevante,
pero queda documentado para no sorprenderse.

## Probar el flujo completo a mano

Requiere que `infra/` ya esté aplicado (`terraform apply`) y que tengas el
`sns_topic_arn` de los outputs.

1. Armar un fixture de prueba (`fixtures/example-price-changes.json`, ver
   `producer/tests/` para el shape) con 2-3 cambios.
2. Publicar:
   ```bash
   cd producer
   uv run renovarte-events-producer publish \
     --input ../fixtures/example-price-changes.json \
     --topic-arn <sns_topic_arn del output de terraform>
   ```
3. Ver logs de la Lambda:
   ```bash
   aws logs tail /aws/lambda/renovarte-events-consumer --follow
   ```
4. Confirmar que el mensaje llega al canal de Discord de prueba.

## Probar el camino de la DLQ

1. Cambiar temporalmente `discord_webhook_url` en `terraform.tfvars` a una
   URL inválida (ej. `https://discord.com/api/webhooks/invalid/invalid`).
2. `terraform apply` (aprobación humana).
3. Publicar un evento de prueba (paso 2 de arriba).
4. Esperar a que la Lambda reintente 5 veces (`maxReceiveCount` de la
   `redrive_policy`) y confirmar que el mensaje aparece en la DLQ:
   ```bash
   aws sqs receive-message --queue-url <sqs_dlq_url del output>
   ```
5. Revertir `discord_webhook_url` al valor real y `terraform apply` de nuevo.

## Desarmar el POC

```bash
cd infra
terraform destroy
```
Requiere aprobación humana explícita — borra recursos reales de AWS.
