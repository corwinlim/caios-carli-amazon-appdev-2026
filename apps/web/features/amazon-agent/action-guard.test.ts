import { describe, expect, it } from "vitest";
import { prepareConfirmedAction, verifyConfirmedAction } from "./action-guard";

const NOW = Date.parse("2026-09-13T20:00:00+08:00");
const ACTION = "record_observation";
const PAYLOAD = {
  pet_id: "pika-demo",
  observation_type: "meal",
  value: "did not finish dinner",
};

describe("Amazon agent ActionGuard", () => {
  it("accepts only the exact confirmed payload before expiry", () => {
    const prepared = prepareConfirmedAction(ACTION, PAYLOAD, {
      now_ms: NOW,
      ttl_ms: 60_000,
    });

    expect(
      verifyConfirmedAction(ACTION, PAYLOAD, prepared.confirmation_token, {
        now_ms: NOW + 30_000,
      }),
    ).toBe(true);
  });

  it("rejects a missing confirmation token", () => {
    expect(() => verifyConfirmedAction(ACTION, PAYLOAD, "", { now_ms: NOW })).toThrow(
      "confirmation token is required",
    );
  });

  it("rejects an expired confirmation token", () => {
    const prepared = prepareConfirmedAction(ACTION, PAYLOAD, {
      now_ms: NOW,
      ttl_ms: 1_000,
    });

    expect(() =>
      verifyConfirmedAction(ACTION, PAYLOAD, prepared.confirmation_token, {
        now_ms: NOW + 1_001,
      }),
    ).toThrow("confirmation token has expired");
  });

  it("rejects a confirmation token when the approved payload changes", () => {
    const prepared = prepareConfirmedAction(ACTION, PAYLOAD, {
      now_ms: NOW,
      ttl_ms: 60_000,
    });

    expect(() =>
      verifyConfirmedAction(
        ACTION,
        { ...PAYLOAD, value: "finished all dinner" },
        prepared.confirmation_token,
        { now_ms: NOW + 10_000 },
      ),
    ).toThrow("confirmation token does not match action payload");
  });
});
