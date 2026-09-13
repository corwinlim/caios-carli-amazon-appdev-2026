import { createHash, timingSafeEqual } from "node:crypto";

type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };

type ClockOptions = {
  now_ms?: number;
  ttl_ms?: number;
};

const DEFAULT_TTL_MS = 60_000;
const DEMO_CONFIRMATION_NAMESPACE = "caios-amazon-agent-synthetic-confirmation-v1";

function normalize(value: unknown): JsonValue {
  if (value === null || typeof value === "boolean" || typeof value === "number" || typeof value === "string") {
    return value;
  }
  if (Array.isArray(value)) return value.map(normalize);
  if (typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([key, item]) => [key, normalize(item)]),
    );
  }
  throw new Error("confirmation payload must be JSON serializable");
}

function digest(actionName: string, payload: unknown, expiresAtMs: number): string {
  const normalized = JSON.stringify(normalize(payload));
  return createHash("sha256")
    .update(DEMO_CONFIRMATION_NAMESPACE)
    .update("\n")
    .update(actionName)
    .update("\n")
    .update(normalized)
    .update("\n")
    .update(String(expiresAtMs))
    .digest("hex");
}

export function prepareConfirmedAction(actionName: string, payload: unknown, options: ClockOptions = {}) {
  const nowMs = options.now_ms ?? Date.now();
  const ttlMs = options.ttl_ms ?? DEFAULT_TTL_MS;
  if (ttlMs <= 0) throw new Error("confirmation ttl must be positive");
  const expiresAtMs = nowMs + ttlMs;
  const payloadDigest = digest(actionName, payload, expiresAtMs);
  return {
    confirmation_token: `${expiresAtMs}.${payloadDigest}`,
    expires_at: new Date(expiresAtMs).toISOString(),
  };
}

export function verifyConfirmedAction(
  actionName: string,
  payload: unknown,
  confirmationToken: string,
  options: Pick<ClockOptions, "now_ms"> = {},
): true {
  if (!confirmationToken) throw new Error("confirmation token is required");
  const separator = confirmationToken.indexOf(".");
  if (separator <= 0) throw new Error("confirmation token is invalid");

  const expiresAtMs = Number(confirmationToken.slice(0, separator));
  const suppliedDigest = confirmationToken.slice(separator + 1);
  if (!Number.isFinite(expiresAtMs) || !suppliedDigest) throw new Error("confirmation token is invalid");

  const nowMs = options.now_ms ?? Date.now();
  if (nowMs > expiresAtMs) throw new Error("confirmation token has expired");

  const expectedDigest = digest(actionName, payload, expiresAtMs);
  const supplied = Buffer.from(suppliedDigest, "utf8");
  const expected = Buffer.from(expectedDigest, "utf8");
  if (supplied.length !== expected.length || !timingSafeEqual(supplied, expected)) {
    throw new Error("confirmation token does not match action payload");
  }

  return true;
}
