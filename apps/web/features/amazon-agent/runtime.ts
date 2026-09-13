export type AgentRuntimeRequest = {
  prompt: string;
  pet_id: string;
  context: Record<string, unknown>;
};

export type AgentRuntimeResult = {
  text: string;
  provider: "deterministic" | "aws-agentcore";
  model: string;
  synthetic: boolean;
  metadata: Record<string, string | number | boolean | null>;
};

export interface AgentRuntime {
  invoke(request: AgentRuntimeRequest): Promise<AgentRuntimeResult>;
}

export class DeterministicAgentRuntime implements AgentRuntime {
  async invoke(request: AgentRuntimeRequest): Promise<AgentRuntimeResult> {
    const petName = request.pet_id === "pika-demo" ? "Pika" : "the pet";
    return {
      text: `${petName}: deterministic fallback prepared the bounded context without external model reasoning.`,
      provider: "deterministic",
      model: "local-fallback",
      synthetic: Boolean(request.context.synthetic ?? false),
      metadata: { degraded_mode: true },
    };
  }
}

type AgentCoreHttpRuntimeOptions = {
  endpoint: string;
  fetcher?: typeof fetch;
  timeout_ms?: number;
};

export class AgentCoreHttpRuntime implements AgentRuntime {
  private readonly endpoint: string;
  private readonly fetcher: typeof fetch;
  private readonly timeoutMs: number;

  constructor(options: AgentCoreHttpRuntimeOptions) {
    if (!options.endpoint.startsWith("https://")) throw new Error("AgentCore endpoint must use HTTPS");
    this.endpoint = options.endpoint;
    this.fetcher = options.fetcher ?? fetch;
    this.timeoutMs = options.timeout_ms ?? 10_000;
  }

  async invoke(request: AgentRuntimeRequest): Promise<AgentRuntimeResult> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const response = await this.fetcher(this.endpoint, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(request),
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`AgentCore invocation failed: ${response.status}`);
      const payload = (await response.json()) as { result?: string; response?: string; model?: string };
      const text = payload.result ?? payload.response;
      if (!text || typeof text !== "string") throw new Error("AgentCore response did not contain a text result");
      return {
        text,
        provider: "aws-agentcore",
        model: payload.model ?? "bedrock-via-agentcore",
        synthetic: Boolean(request.context.synthetic ?? false),
        metadata: { degraded_mode: false },
      };
    } finally {
      clearTimeout(timeout);
    }
  }
}

export function createAgentRuntimeFromEnv(): AgentRuntime {
  const endpoint = process.env.AMAZON_AGENTCORE_ENDPOINT;
  if (!endpoint) return new DeterministicAgentRuntime();
  return new AgentCoreHttpRuntime({ endpoint });
}
