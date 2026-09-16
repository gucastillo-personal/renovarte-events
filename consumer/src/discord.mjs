const KIND_EMOJI = {
  price_up: "📈",
  price_down: "📉",
  added: "🆕",
  removed: "🗑️",
};

const MAX_LINES = 10;

function formatPrice(value) {
  return value === null ? null : `$${value.toLocaleString("es-AR")}`;
}

function formatChangeLine(change) {
  const emoji = KIND_EMOJI[change.kind] ?? "•";
  switch (change.kind) {
    case "price_up":
    case "price_down":
      return `${emoji} ${change.nombre}: ${formatPrice(change.old_price)} → ${formatPrice(change.new_price)}`;
    case "added":
      return `${emoji} ${change.nombre}: ${formatPrice(change.new_price)}`;
    case "removed":
      return `${emoji} ${change.nombre}`;
    default:
      return `${emoji} ${change.nombre}`;
  }
}

function formatDate(isoString) {
  const date = new Date(isoString);
  return Number.isNaN(date.getTime()) ? isoString : date.toLocaleDateString("es-AR", { timeZone: "UTC" });
}

function buildSummaryLine(summary) {
  const parts = [
    summary.added ? `${summary.added} nuevo${summary.added === 1 ? "" : "s"}` : null,
    summary.removed ? `${summary.removed} eliminado${summary.removed === 1 ? "" : "s"}` : null,
    summary.price_up ? `${summary.price_up} ${summary.price_up === 1 ? "subió" : "subieron"}` : null,
    summary.price_down ? `${summary.price_down} ${summary.price_down === 1 ? "bajó" : "bajaron"}` : null,
  ].filter(Boolean);

  return parts.length > 0 ? parts.join(" · ") : "sin cambios";
}

export function buildDiscordMessage(payload) {
  const { summary, changes, generated_at: generatedAt } = payload;

  const shownLines = changes.slice(0, MAX_LINES).map(formatChangeLine);
  const remaining = changes.length - shownLines.length;
  if (remaining > 0) shownLines.push(`…y ${remaining} más`);

  const content = [
    `**RenovArte — cambios de precio (${formatDate(generatedAt)})**`,
    buildSummaryLine(summary),
    "",
    ...shownLines,
  ].join("\n");

  return { content };
}
