"use client";

import { useState } from "react";

const OBSERVATION_PAYLOAD = {
  pet_id: "pika-demo",
  observed_at: "2026-09-13T18:45:00+08:00",
  observation_type: "meal",
  value: "did not finish dinner",
  source: "owner" as const,
  severity: "mild" as const,
  notes: "Owner observed lower intake than usual.",
};

type McpEnvelope = {
  result?: { isError?: boolean; content?: Array<{ type: string; text: string }>; structuredContent?: Record<string, unknown> };
  error?: { message?: string };
};

async function callMcpTool(name: string, args: Record<string, unknown>) {
  const response = await fetch("/api/amazon-agent/mcp", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/call", params: { name, arguments: args } }),
  });
  const envelope = (await response.json()) as McpEnvelope;
  if (!response.ok || envelope.error || envelope.result?.isError) {
    throw new Error(envelope.error?.message ?? envelope.result?.content?.[0]?.text ?? "MCP tool call failed");
  }
  return envelope.result?.structuredContent ?? {};
}

async function confirmAction(action: string, payload: Record<string, unknown>) {
  const response = await fetch("/api/amazon-agent/confirmation", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ action, payload }),
  });
  const data = (await response.json()) as { confirmation_token?: string; error?: string };
  if (!response.ok || !data.confirmation_token) throw new Error(data.error ?? "Unable to confirm action");
  return data.confirmation_token;
}

export function JudgeSimulator() {
  const [pendingObservation, setPendingObservation] = useState(false);
  const [status, setStatus] = useState("Ready for the judge flow.");
  const [busy, setBusy] = useState(false);

  function prepareDinnerObservation() {
    setPendingObservation(true);
    setStatus("Observation prepared locally. No write has occurred.");
  }

  async function approveObservation() {
    setBusy(true);
    try {
      const confirmationToken = await confirmAction("record_observation", OBSERVATION_PAYLOAD);
      await callMcpTool("record_observation", { ...OBSERVATION_PAYLOAD, confirmation_token: confirmationToken });
      setPendingObservation(false);
      setStatus("CARE EVENT INPUT RECORDED — owner-approved synthetic observation written through MCP.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to record observation.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-labelledby="amazon-agent-title" className="mx-auto max-w-4xl space-y-6 p-6">
      <header className="space-y-3">
        <div className="flex flex-wrap gap-2 text-xs font-semibold uppercase tracking-wide">
          <span className="rounded-full border px-3 py-1">Synthetic demo</span>
          <span className="rounded-full border px-3 py-1">Non-diagnostic</span>
          <span className="rounded-full border px-3 py-1">Alexa+ / MCP</span>
        </div>
        <h1 id="amazon-agent-title" className="text-3xl font-semibold">CAIOS × CARLI Home Pet Agent</h1>
        <p className="max-w-2xl text-sm leading-6 opacity-80">
          Pika&apos;s longitudinal context stays bounded inside CAIOS. CARLI prepares an action, waits for owner approval, then executes the exact approved payload through the same MCP gateway used by the agent.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        <article className="rounded-2xl border p-5">
          <p className="text-xs font-semibold uppercase tracking-wide opacity-60">Scenario</p>
          <h2 className="mt-2 text-xl font-semibold">Pika is home this evening</h2>
          <p className="mt-2 text-sm leading-6 opacity-80">The owner notices that Pika did not finish dinner and asks CARLI to record the change without turning a casual observation into an autonomous medical decision.</p>
          <button type="button" onClick={prepareDinnerObservation} disabled={busy} className="mt-5 rounded-xl border px-4 py-3 text-sm font-semibold">Pika didn&apos;t finish dinner</button>
        </article>

        <article className="rounded-2xl border p-5" aria-live="polite">
          <p className="text-xs font-semibold uppercase tracking-wide opacity-60">Agent trace</p>
          <p className="mt-3 text-sm leading-6">{status}</p>
          {pendingObservation ? (
            <div className="mt-5 rounded-xl border p-4">
              <strong className="block text-sm">Owner Approval Required</strong>
              <p className="mt-2 text-sm opacity-80">Record: “Pika did not finish dinner” as a mild owner-reported meal observation.</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <button type="button" onClick={approveObservation} disabled={busy} className="rounded-lg border px-3 py-2 text-sm font-semibold">{busy ? "Recording…" : "Approve & Record"}</button>
                <button type="button" onClick={() => { setPendingObservation(false); setStatus("Action cancelled. No write occurred."); }} disabled={busy} className="rounded-lg border px-3 py-2 text-sm">Cancel</button>
              </div>
            </div>
          ) : null}
        </article>
      </div>

      <footer className="rounded-2xl border p-4 text-xs leading-5 opacity-70">Demo boundary: synthetic Pika data only. This interface does not diagnose, prescribe, or replace veterinary judgment. Consequential writes require explicit owner confirmation.</footer>
    </section>
  );
}
