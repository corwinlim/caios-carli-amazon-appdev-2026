import type { PetEventCreate } from "@caios/sdk";

export type CanonicalCareInput = {
  pet_id: string;
  action_id: string;
  action_type: string;
  actor: string;
  approved_by_owner: boolean;
  executed_at: string;
  outcome: string;
  source: string;
  runtime_provider: "deterministic" | "aws-agentcore";
  runtime_model: string;
};

export function toCanonicalCareEvent(input: CanonicalCareInput): PetEventCreate {
  if (!input.approved_by_owner) {
    throw new Error("Canonical care write-back requires explicit owner approval");
  }

  return {
    event_type: "OBSERVATION",
    title: `CARLI care action: ${input.action_type}`,
    notes: input.outcome,
    occurred_at: input.executed_at,
    source: "SYSTEM",
    source_type: "DERIVED",
    source_id: input.action_id,
    idempotency_key: `carli:${input.action_id}`,
    raw_input: null,
    metadata: {
      care_action_type: input.action_type,
      actor: input.actor,
      approved_by_owner: input.approved_by_owner,
      integration_source: input.source,
      runtime_provider: input.runtime_provider,
      runtime_model: input.runtime_model,
    },
    importance: 3,
    payload: {
      category: "care_action",
      observation: input.outcome,
    },
  };
}
