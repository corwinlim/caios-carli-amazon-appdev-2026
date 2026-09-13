import { z } from "zod";
import {
  AMAZON_AGENT_TOOLS,
  createFollowUpInput,
  generateHealthStoryInput,
  getPetContextInput,
  getRecentChangesInput,
  getTodaySummaryInput,
  recordObservationInput,
} from "./contracts";
import { generateHealthStory, getPetContext, getRecentChanges, getTodaySummary } from "./context-provider";
import { createFollowUp, recordObservation } from "./store";

type ToolResult = {
  content: Array<{ type: "text"; text: string }>;
  structuredContent: Record<string, unknown>;
  isError: boolean;
};

function success(data: unknown): ToolResult {
  return {
    content: [{ type: "text", text: JSON.stringify(data) }],
    structuredContent: data as Record<string, unknown>,
    isError: false,
  };
}

function failure(message: string): ToolResult {
  return {
    content: [{ type: "text", text: message }],
    structuredContent: { error: message },
    isError: true,
  };
}

function invalidInput(error: z.ZodError): ToolResult {
  const details = error.issues.map((issue) => `${issue.path.join(".") || "input"}: ${issue.message}`).join("; ");
  return failure(`Invalid tool input: ${details}`);
}

export function listAmazonAgentTools() {
  return AMAZON_AGENT_TOOLS.map((tool) => ({
    name: tool.name,
    description: tool.description,
    inputSchema: z.toJSONSchema(tool.inputSchema),
    annotations: {
      readOnlyHint: tool.readOnly,
      destructiveHint: false,
      idempotentHint: tool.readOnly,
      openWorldHint: false,
    },
  }));
}

export function dispatchAmazonAgentTool(name: string, input: unknown): ToolResult {
  try {
    switch (name) {
      case "get_pet_context": {
        const parsed = getPetContextInput.safeParse(input);
        if (!parsed.success) return invalidInput(parsed.error);
        return success(getPetContext(parsed.data.pet_id));
      }
      case "get_today_summary": {
        const parsed = getTodaySummaryInput.safeParse(input);
        if (!parsed.success) return invalidInput(parsed.error);
        return success(getTodaySummary(parsed.data.pet_id, parsed.data.date));
      }
      case "get_recent_changes": {
        const parsed = getRecentChangesInput.safeParse(input);
        if (!parsed.success) return invalidInput(parsed.error);
        return success(getRecentChanges(parsed.data.pet_id, parsed.data.window_days));
      }
      case "generate_health_story": {
        const parsed = generateHealthStoryInput.safeParse(input);
        if (!parsed.success) return invalidInput(parsed.error);
        return success(generateHealthStory(parsed.data.pet_id, parsed.data.window_days));
      }
      case "record_observation": {
        const parsed = recordObservationInput.safeParse(input);
        if (!parsed.success) return invalidInput(parsed.error);
        const { confirmation_token, ...payload } = parsed.data;
        return success(recordObservation(payload, confirmation_token));
      }
      case "create_follow_up": {
        const parsed = createFollowUpInput.safeParse(input);
        if (!parsed.success) return invalidInput(parsed.error);
        const { confirmation_token, ...payload } = parsed.data;
        return success(createFollowUp(payload, confirmation_token));
      }
      default:
        return failure(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return failure(error instanceof Error ? error.message : "Tool execution failed");
  }
}
