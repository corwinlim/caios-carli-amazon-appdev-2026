import { verifyConfirmedAction } from "./action-guard";

export type SyntheticObservationRecord = {
  id: string;
  pet_id: string;
  observed_at: string;
  observation_type: string;
  value: string;
  source: "owner" | "voice" | "vision" | "device" | "demo";
  severity: "none" | "mild" | "moderate" | "high";
  notes?: string;
  created_at: string;
};

export type SyntheticFollowUpRecord = {
  id: string;
  pet_id: string;
  reason: string;
  due_at: string;
  created_at: string;
};

type ObservationInput = Omit<SyntheticObservationRecord, "id" | "created_at">;
type FollowUpInput = Omit<SyntheticFollowUpRecord, "id" | "created_at">;

const state: { observations: SyntheticObservationRecord[]; follow_ups: SyntheticFollowUpRecord[] } = {
  observations: [],
  follow_ups: [],
};

let sequence = 0;
function nextId(prefix: string) {
  sequence += 1;
  return `${prefix}-${sequence}`;
}

export function getDemoState() {
  return { observations: [...state.observations], follow_ups: [...state.follow_ups] };
}

export function resetDemoState() {
  state.observations = [];
  state.follow_ups = [];
  sequence = 0;
}

export function recordObservation(input: ObservationInput, confirmationToken: string): SyntheticObservationRecord {
  verifyConfirmedAction("record_observation", input, confirmationToken);
  const created: SyntheticObservationRecord = { ...input, id: nextId("observation"), created_at: new Date().toISOString() };
  state.observations.push(created);
  return created;
}

export function createFollowUp(input: FollowUpInput, confirmationToken: string): SyntheticFollowUpRecord {
  verifyConfirmedAction("create_follow_up", input, confirmationToken);
  const created: SyntheticFollowUpRecord = { ...input, id: nextId("follow-up"), created_at: new Date().toISOString() };
  state.follow_ups.push(created);
  return created;
}
