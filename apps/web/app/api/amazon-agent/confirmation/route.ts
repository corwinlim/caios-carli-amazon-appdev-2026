import { NextRequest, NextResponse } from "next/server";

import { prepareConfirmedAction } from "@/features/amazon-agent/action-guard";

const ALLOWED_ACTIONS = new Set(["record_observation", "create_follow_up"]);

export async function POST(request: NextRequest) {
  let body: { action?: string; payload?: unknown };
  try {
    body = (await request.json()) as { action?: string; payload?: unknown };
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  if (!body.action || !ALLOWED_ACTIONS.has(body.action)) {
    return NextResponse.json({ error: "Unsupported confirmation action" }, { status: 400 });
  }
  if (body.payload === undefined) {
    return NextResponse.json({ error: "Confirmation payload is required" }, { status: 400 });
  }

  const prepared = prepareConfirmedAction(body.action, body.payload);
  return NextResponse.json({
    ...prepared,
    action: body.action,
    synthetic: true,
    message: "Owner approval recorded for this exact synthetic demo payload only.",
  });
}
