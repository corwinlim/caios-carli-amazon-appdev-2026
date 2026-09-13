export type PetEventCreate = {
  event_type: "OBSERVATION";
  title: string;
  notes: string;
  occurred_at: string;
  source: "SYSTEM";
  source_type: "DERIVED";
  source_id: string | null;
  idempotency_key: string | null;
  raw_input: string | null;
  metadata: Record<string, string | number | boolean | null>;
  importance: number;
  payload: {
    category: string;
    observation: string;
  };
};
