# Amazon AppDev 2026 — AWS Live Proof

Status: PASS for live Amazon Bedrock AgentCore Runtime proof.

Date: 2026-09-13 (Malaysia time)
Region: `us-west-2`
Runtime: `CaiosAmazonMcpProof`
Protocol: MCP
Runtime status: `READY`

> Public disclosure note: this evidence intentionally omits the AWS account ID, full runtime ARN, IAM role ARN, ECR URI, and credentials. Those values remain private operational metadata.

## Control-plane proof

AWS `GetAgentRuntime` returned:

- Runtime name: `CaiosAmazonMcpProof`
- Description: `CAIOS Home Pet Agent synthetic MCP proof for Amazon 2026 hackathon`
- Status: `READY`
- Server protocol: `MCP`
- Network mode: `PUBLIC`
- Runtime version: `1`

The AWS account also returned a non-empty Amazon Bedrock foundation-model catalog in `us-west-2`, confirming Bedrock service visibility in the same account/region.

## Invocation proof

### 1. MCP initialize

`InvokeAgentRuntime` succeeded with:

- HTTP status: `200`
- Response content type: `text/event-stream`
- MCP protocol negotiated: `2025-11-25`
- Server: `CAIOS Home Pet Agent`
- Server version: `1.30.0`

### 2. MCP tools/list

`InvokeAgentRuntime` `tools/list` succeeded with HTTP 200 and returned exactly six tools:

1. `get_pet_context`
2. `get_today_summary`
3. `get_recent_changes`
4. `record_observation`
5. `create_follow_up`
6. `generate_health_story`

This matches the repository's Amazon Agent tool registry.

### 3. Safe read-only tool call

`InvokeAgentRuntime` `tools/call` for `get_pet_context` succeeded with HTTP 200 using `pet_id=pika-demo`.

The returned tool result identified Pika as a synthetic, non-diagnostic Pomeranian demo pet. No mutating tool was invoked for this proof.

## Claim boundary

The submission may truthfully claim:

- A real Amazon Bedrock AgentCore Runtime is deployed and READY.
- The deployed runtime implements MCP and negotiates protocol version `2025-11-25`.
- The runtime exposes the six CAIOS Home Pet Agent tools.
- A real read-only MCP tool invocation completed successfully through `InvokeAgentRuntime`.

The submission must not claim that the new Strands/Bedrock TypeScript sidecar has been separately deployed unless deployment evidence is added later.
