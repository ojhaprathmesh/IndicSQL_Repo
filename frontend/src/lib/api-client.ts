import {
  BackendHealthResponse,
  ProjectAnalytics,
  QueryResponse,
  SchemasResponse,
  SqlInspectResponse,
  VoiceSynthesizeRequest,
  VoiceSynthesizeResponse,
  VoiceTranscribeResponse,
} from "@/types/api";

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
).replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiError(
      `Could not connect to the IndicSQL backend at ${API_BASE_URL}.`,
      0
    );
  }

  if (!response.ok) {
    let message = `Backend request failed (${response.status}).`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (body.detail !== undefined) {
        message = JSON.stringify(body.detail);
      }
    } catch {
      // Keep the HTTP status message when the backend returns a non-JSON error.
    }
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

export const apiClient = {
  checkHealth(): Promise<BackendHealthResponse> {
    return request<BackendHealthResponse>("/health");
  },

  fetchSchemas(): Promise<SchemasResponse> {
    return request<SchemasResponse>("/schemas");
  },

  fetchAnalytics(): Promise<ProjectAnalytics> {
    return request<ProjectAnalytics>("/analytics");
  },

  inspectSql(sql: string): Promise<SqlInspectResponse> {
    return request<SqlInspectResponse>("/sql/inspect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sql }),
    });
  },

  submitQuery(query: string, signal?: AbortSignal): Promise<QueryResponse> {
    return request<QueryResponse>("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
      signal,
    });
  },

  transcribeAudio(audio: Blob): Promise<VoiceTranscribeResponse> {
    const formData = new FormData();
    formData.append("file", audio, "recording.wav");
    return request<VoiceTranscribeResponse>("/voice/transcribe", {
      method: "POST",
      body: formData,
    });
  },

  synthesizeSpeech(
    payload: VoiceSynthesizeRequest
  ): Promise<VoiceSynthesizeResponse> {
    return request<VoiceSynthesizeResponse>("/voice/synthesize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },
};
