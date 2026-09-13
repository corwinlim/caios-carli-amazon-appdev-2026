import { NextRequest, NextResponse } from "next/server";
import { dispatchAmazonAgentTool, listAmazonAgentTools } from "@/features/amazon-agent/dispatcher";

const MCP_PROTOCOL_VERSION = "2025-11-25";
const SERVER_INFO = { name: "caios-carli-amazon-agent", version: "0.1.0" };

type JsonRpcRequest = {
  jsonrpc?: string;
  id?: string | number | null;
  method?: string;
  params?: Record<string, unknown>;
};

function jsonRpcResult(id: JsonRpcRequest["id"], result: unknown, status = 200) {
  return NextResponse.json({ jsonrpc: "2.0", id: id ?? null, result }, { status });
}

function jsonRpcError(id: JsonRpcRequest["id"], code: number, message: string, status = 200) {
  return NextResponse.json({ jsonrpc: "2.0", id: id ?? null, error: { code, message } }, { status });
}

export async function POST(request: NextRequest) {
  let body: JsonRpcRequest;
  try {
    body = (await request.json()) as JsonRpcRequest;
  } catch {
    return jsonRpcError(null, -32700, "Parse error", 400);
  }

  if (body.jsonrpc !== "2.0" || !body.method) {
    return jsonRpcError(body.id, -32600, "Invalid Request", 400);
  }

  if (body.method === "notifications/initialized") {
    return new NextResponse(null, { status: 202 });
  }

  if (body.method === "initialize") {
    const requestedVersion = String(body.params?.protocolVersion ?? MCP_PROTOCOL_VERSION);
    const protocolVersion = requestedVersion === MCP_PROTOCOL_VERSION ? requestedVersion : MCP_PROTOCOL_VERSION;
    return jsonRpcResult(body.id, {
      protocolVersion,
      capabilities: { tools: { listChanged: false } },
      serverInfo: SERVER_INFO,
      instructions: "Synthetic Pika demo only. Read tools are non-diagnostic; mutating tools require explicit owner confirmation.",
    });
  }

  if (body.method === "tools/list") {
    return jsonRpcResult(body.id, { tools: listAmazonAgentTools() });
  }

  if (body.method === "tools/call") {
    const name = typeof body.params?.name === "string" ? body.params.name : "";
    const args = body.params?.arguments ?? {};
    if (!name) return jsonRpcError(body.id, -32602, "Invalid params: tool name is required");
    return jsonRpcResult(body.id, dispatchAmazonAgentTool(name, args));
  }

  return jsonRpcError(body.id, -32601, `Method not found: ${body.method}`);
}

export function GET() {
  return new NextResponse(null, { status: 405, headers: { Allow: "POST" } });
}

export function DELETE() {
  return new NextResponse(null, { status: 405, headers: { Allow: "POST" } });
}
