import type { Company } from "@/components/assistant/data";

export const API_BASE_URL: string =
  (typeof import.meta !== "undefined" && import.meta.env?.["VITE_API_BASE_URL"]) ||
  "https://13-126-246-11.sslip.io";

let baseUrl = API_BASE_URL;
export const getApiBaseUrl = () => baseUrl;
export const setApiBaseUrl = (url: string) => {
  baseUrl = url.trim().replace(/\/+$/, "") || API_BASE_URL;
};

export type BackendCompany = "darglobal" | "wasalt" | "all";
export const mapCompany = (c: Company): BackendCompany =>
  c === "DarGlobal" ? "darglobal" : c === "Wasalt" ? "wasalt" : "all";

export type BackendSource = {
  chunk_id?: string;
  title?: string;
  company?: string;
  category?: string;
  source_url?: string;
  content_snippet?: string;
  relevance_score?: number;
};
export type ChatResponse = {
  answer: string;
  company?: string;
  model_used?: string;
  model?: string;
  sources: BackendSource[];
  retrieval_method?: string;
  fallback_applied?: boolean;
  disclaimer?: string;
  [key: string]: unknown;
};
export type HealthResponse = {
  status?: string;
  chunks_indexed?: number;
  total_chunks?: number;
  chunks?: number;
  embedding_model?: string;
  vector_index?: string;
  vector_store?: string;
  openrouter_configured?: boolean;
  active_model?: string;
  model?: string;
  llm_model?: string;
  provider?: string;
  ai_provider?: string;
  version?: string;
  [key: string]: unknown;
};
export type SourcesResponse = {
  total_chunks?: number;
  darglobal_chunks?: number;
  wasalt_chunks?: number;
  categories?: Record<string, number>;
  primary_documents?: string[];
  companies?: Record<
    string,
    { chunks?: number; total_chunks?: number; categories?: Record<string, number> | string[] }
  >;
  [key: string]: unknown;
};
export type SearchResponse = { results?: BackendSource[]; [key: string]: unknown };

async function request<T>(path: string, init?: RequestInit, timeoutMs = 60000): Promise<T> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(`${baseUrl}${path}`, {
      ...init,
      signal: init?.signal ?? ctrl.signal,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
    if (!res.ok) {
      let detail = "";
      try {
        const body = await res.json();
        detail = typeof body?.detail === "string" ? body.detail : "";
      } catch {
        /* ignore */
      }
      throw new Error(detail || `Backend responded with ${res.status}`);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(t);
  }
}

export const checkBackendHealth = () => request<HealthResponse>("/health", undefined, 8000);

export const askChatbot = (query: string, _company: Company, topK = 5, signal?: AbortSignal) =>
  request<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ query, company: "all", top_k: topK }),
    signal: signal ?? null,
  });

export const fetchKnowledgeSources = () => request<SourcesResponse>("/sources");

export const searchKnowledge = (query: string, _company: Company, topK = 5) =>
  request<SearchResponse>("/search", {
    method: "POST",
    body: JSON.stringify({ query, company: "all", top_k: topK }),
  });

export const healthChunks = (h?: HealthResponse | null) =>
  (h?.chunks_indexed ?? h?.total_chunks ?? 132) as number;
export const healthModel = (h?: HealthResponse | null) =>
  (h?.active_model ?? h?.model ?? "google/gemma-4-31b-it:free") as string;
// Display name: drops the OpenRouter ":free" pricing suffix from a model id.
export const modelLabel = (m?: string | null) => (m || "").replace(/:free$/i, "");
export const healthProvider = (h?: HealthResponse | null) =>
  (h?.provider ??
    h?.ai_provider ??
    (h?.openrouter_configured === false ? "Not configured" : "OpenRouter")) as string;
export const healthVectorStore = (h?: HealthResponse | null) =>
  (h?.vector_index ?? h?.vector_store ?? "FAISS IndexFlatIP") as string;

// /sources reports a single flat category map for both collections, while the UI
// lists human-readable labels. Map each label onto the payload's category key.
const CATEGORY_KEYS: Record<string, string> = {
  brand_partnerships: "brand_partners",
  services_and_taxonomy: "taxonomy",
  property_listings: "listings",
};
export const sourceCategoryKey = (label: string) => {
  const slug = label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
  return CATEGORY_KEYS[slug] ?? slug;
};
export const sourceCategoryCount = (data: SourcesResponse | null | undefined, label: string) =>
  data?.categories?.[sourceCategoryKey(label)];

export type StreamDonePayload = ChatResponse & {
  ttft_ms?: number;
  total_time_ms?: number;
};

/**
 * Streams an answer from POST /chat/stream (SSE). Never throws: every failure,
 * including non-OK HTTP status, goes to onError so the caller can fall back.
 */
export async function streamChatbot(
  query: string,
  _company: Company,
  topK = 5,
  onToken: (token: string) => void,
  onDone: (done: StreamDonePayload) => void,
  onError: (err: Error) => void,
  signal?: AbortSignal,
): Promise<void> {
  let finished = false;
  const fail = (e: unknown) => {
    if (finished) return;
    finished = true;
    onError(e instanceof Error ? e : new Error(String(e || "Streaming failed")));
  };
  try {
    const res = await fetch(`${baseUrl}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ query, company: "all", top_k: topK }),
      signal: signal ?? null,
    });
    if (!res.ok || !res.body) return fail(new Error(`Streaming unavailable (${res.status})`));
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    const handleLine = (raw: string) => {
      const line = raw.trim();
      if (!line.startsWith("data:")) return;
      const json = line.slice(5).trim();
      if (!json || json === "[DONE]") return;
      let data: { type?: string; token?: string; message?: string } & Record<string, unknown>;
      try {
        data = JSON.parse(json);
      } catch {
        return;
      }
      if (data.type === "token" && typeof data.token === "string") onToken(data.token);
      else if (data.type === "done" && !finished) {
        finished = true;
        onDone(data as unknown as StreamDonePayload);
      } else if (data.type === "error") fail(new Error(data.message || "Streaming failed"));
    };
    while (!finished) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() ?? "";
      for (const l of lines) {
        handleLine(l);
        if (finished) break;
      }
    }
    buffer += decoder.decode();
    if (!finished && buffer) handleLine(buffer);
    if (finished) reader.cancel().catch(() => {});
    else fail(new Error("Stream ended before completion"));
  } catch (e) {
    fail(e);
  }
}
