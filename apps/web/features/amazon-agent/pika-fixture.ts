export type SyntheticObservation = {
  observed_at: string;
  type: "meal" | "activity" | "observation" | "medication" | "follow_up";
  summary: string;
  baseline_change?: string;
};

export type SyntheticPikaFixture = {
  synthetic: true;
  pet: {
    id: "pika-demo";
    name: "Pika";
    species: "DOG";
    breed: "Pomeranian";
  };
  current_plan: {
    feeding: string;
    monitoring: string[];
  };
  observations: SyntheticObservation[];
};

export const PIKA_FIXTURE: SyntheticPikaFixture = {
  synthetic: true,
  pet: {
    id: "pika-demo",
    name: "Pika",
    species: "DOG",
    breed: "Pomeranian",
  },
  current_plan: {
    feeding: "Regular evening meal with owner-observed intake recorded.",
    monitoring: ["appetite", "stool", "activity", "comfort"],
  },
  observations: [
    {
      observed_at: "2026-09-13T10:00:00+08:00",
      type: "activity",
      summary: "Normal morning activity compared with Pika's recent baseline.",
    },
    {
      observed_at: "2026-09-13T18:30:00+08:00",
      type: "meal",
      summary: "Dinner served; intake was lower than usual.",
      baseline_change: "Lower dinner intake than Pika's recent baseline.",
    },
    {
      observed_at: "2026-09-13T19:00:00+08:00",
      type: "observation",
      summary: "Owner noted that Pika did not finish dinner.",
      baseline_change: "Reduced appetite observed this evening.",
    },
  ],
};
