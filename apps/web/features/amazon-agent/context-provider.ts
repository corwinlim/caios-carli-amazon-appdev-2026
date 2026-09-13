import { PIKA_FIXTURE } from "./pika-fixture";

function requireDemoPet(petId: string) {
  if (petId !== PIKA_FIXTURE.pet.id) {
    throw new Error(`Unknown synthetic pet: ${petId}`);
  }
  return PIKA_FIXTURE;
}

export function getPetContext(petId: string) {
  const fixture = requireDemoPet(petId);
  return {
    synthetic: true as const,
    pet: fixture.pet,
    current_plan: fixture.current_plan,
    safety: {
      scope: "demo-only",
      clinical_authority: false,
      message: "Synthetic context for a non-diagnostic hackathon demonstration.",
    },
  };
}

export function getTodaySummary(petId: string, date = "2026-09-13") {
  const fixture = requireDemoPet(petId);
  const observations = fixture.observations.filter((item) => item.observed_at.startsWith(date));
  return {
    pet_id: petId,
    date,
    synthetic: true as const,
    observations,
    summary: observations.map((item) => item.summary).join(" "),
    safety_note: "This summary is informational and does not provide clinical conclusions.",
  };
}

export function getRecentChanges(petId: string, windowDays = 7) {
  const fixture = requireDemoPet(petId);
  return {
    pet_id: petId,
    window_days: windowDays,
    synthetic: true as const,
    changes: fixture.observations
      .filter((item) => item.baseline_change)
      .map((item) => ({
        observed_at: item.observed_at,
        change: item.baseline_change!,
        source_type: item.type,
      })),
  };
}

export function generateHealthStory(petId: string, windowDays = 7) {
  const fixture = requireDemoPet(petId);
  const changes = getRecentChanges(petId, windowDays).changes;
  return {
    pet_id: petId,
    window_days: windowDays,
    synthetic: true as const,
    summary:
      changes.length > 0
        ? `${fixture.pet.name} has mostly maintained her recent routine, with a notable change in dinner intake that should be monitored alongside appetite, stool, activity, and comfort.`
        : `${fixture.pet.name} has no notable synthetic changes recorded in the selected window.`,
    timeline: fixture.observations,
    disclaimer: "Non-diagnostic demo summary. A veterinarian remains the clinical authority.",
  };
}
