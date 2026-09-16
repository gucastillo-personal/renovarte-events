import { test } from "node:test";
import assert from "node:assert/strict";
import { buildDiscordMessage } from "../src/discord.mjs";

test("resume un cambio de cada tipo", () => {
  const payload = {
    generated_at: "2026-09-16T09:00:00Z",
    summary: { added: 1, removed: 1, price_up: 1, price_down: 1, total: 4 },
    changes: [
      { kind: "price_up", id: "1", nombre: "Latex Interior 20L", old_price: 38000, new_price: 41000 },
      { kind: "price_down", id: "2", nombre: "Esmalte Sintético 4L", old_price: 15900, new_price: 13900 },
      { kind: "added", id: "3", nombre: "Rodillo Antigota 23cm", old_price: null, new_price: 4200 },
      { kind: "removed", id: "4", nombre: "Lija al Agua 220", old_price: 1500, new_price: null },
    ],
  };

  const message = buildDiscordMessage(payload);

  assert.match(message.content, /1 nuevo/);
  assert.match(message.content, /1 eliminado/);
  assert.match(message.content, /1 subió/);
  assert.match(message.content, /1 bajó/);
  assert.match(message.content, /Latex Interior 20L/);
});

test("sin cambios muestra el resumen vacío sin romper", () => {
  const payload = {
    generated_at: "2026-09-16T09:00:00Z",
    summary: { added: 0, removed: 0, price_up: 0, price_down: 0, total: 0 },
    changes: [],
  };

  const message = buildDiscordMessage(payload);

  assert.match(message.content, /sin cambios/);
});

test("trunca a MAX_LINES y muestra cuántos quedaron afuera", () => {
  const changes = Array.from({ length: 25 }, (_, i) => ({
    kind: "added",
    id: `srl-${i}`,
    nombre: `Producto ${i}`,
    old_price: null,
    new_price: 100,
  }));
  const payload = {
    generated_at: "2026-09-16T09:00:00Z",
    summary: { added: 25, removed: 0, price_up: 0, price_down: 0, total: 25 },
    changes,
  };

  const message = buildDiscordMessage(payload);

  assert.match(message.content, /…y 15 más/);
});
