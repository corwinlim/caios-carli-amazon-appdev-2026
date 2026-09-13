import { z } from "zod";

const petIdSchema = z.object({ pet_id: z.string().min(1) });

export const getPetContextInput = petIdSchema;
export const getTodaySummaryInput = petIdSchema.extend({
  date: z.string().optional(),
});
export const getRecentChangesInput = petIdSchema.extend({
  window_days: z.number().int().min(1).max(90).default(7),
});
export const recordObservationInput = z.object({
  pet_id: z.string().min(1),
  observed_at: z.string().min(1),
  observation_type: z.string().min(1),
  value: z.string().min(1),
  source: z.enum(["owner", "voice", "vision", "device", "demo"]),
  severity: z.enum(["none", "mild", "moderate", "high"]),
  notes: z.string().optional(),
  confirmation_token: z.string().min(1),
});
export const createFollowUpInput = z.object({
  pet_id: z.string().min(1),
  reason: z.string().min(1),
  due_at: z.string().min(1),
  confirmation_token: z.string().min(1),
});
export const generateHealthStoryInput = petIdSchema.extend({
  window_days: z.number().int().min(1).max(90).default(7),
});

export const AMAZON_AGENT_TOOLS = [
  { name: "get_pet_context", description: "Retrieve synthetic longitudinal context for a demo pet without mutating state.", inputSchema: getPetContextInput, readOnly: true },
  { name: "get_today_summary", description: "Summarize today's synthetic meals, activity, observations, medications, and follow-ups.", inputSchema: getTodaySummaryInput, readOnly: true },
  { name: "get_recent_changes", description: "Compare recent synthetic observations with the pet's own baseline and return notable changes.", inputSchema: getRecentChangesInput, readOnly: true },
  { name: "record_observation", description: "Record a canonical synthetic pet observation after explicit user confirmation has been verified.", inputSchema: recordObservationInput, readOnly: false },
  { name: "create_follow_up", description: "Create a synthetic follow-up task after explicit user confirmation has been verified.", inputSchema: createFollowUpInput, readOnly: false },
  { name: "generate_health_story", description: "Generate a concise non-diagnostic longitudinal health story from synthetic pet context.", inputSchema: generateHealthStoryInput, readOnly: true },
] as const;

export type AmazonAgentToolName = (typeof AMAZON_AGENT_TOOLS)[number]["name"];
