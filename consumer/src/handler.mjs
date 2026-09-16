import { buildDiscordMessage } from "./discord.mjs";

// Entry point de la Lambda (event source mapping SQS -> Lambda, ver
// infra/lambda.tf). Reporta fallas parciales del batch (`batchItemFailures`)
// en vez de relanzar para todo el lote: así solo el mensaje que falló
// reintenta (y eventualmente cae en la DLQ), sin reprocesar los que ya se
// entregaron a Discord.
export const handler = async (event) => {
  const batchItemFailures = [];

  for (const record of event.Records ?? []) {
    try {
      const payload = JSON.parse(record.body);
      const message = buildDiscordMessage(payload);
      const response = await fetch(process.env.DISCORD_WEBHOOK_URL, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(message),
      });
      if (!response.ok) {
        throw new Error(`Discord respondió ${response.status}`);
      }
    } catch (error) {
      console.error("Fallo procesando mensaje", record.messageId, error);
      batchItemFailures.push({ itemIdentifier: record.messageId });
    }
  }

  return { batchItemFailures };
};
