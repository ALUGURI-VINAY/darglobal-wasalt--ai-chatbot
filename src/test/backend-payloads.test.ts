import { describe, expect, it } from "vitest";
import {
  healthChunks,
  healthModel,
  healthProvider,
  healthVectorStore,
  modelLabel,
  sourceCategoryCount,
  type HealthResponse,
  type SourcesResponse,
} from "@/lib/api";
import { companyStats } from "@/components/assistant/shell";

const health: HealthResponse = {
  status: "healthy",
  chunks_indexed: 132,
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2",
  vector_index: "FAISS_IndexFlatIP",
  openrouter_configured: true,
  active_model: "google/gemma-4-31b-it:free",
  version: "1.0.0",
};

const sources: SourcesResponse = {
  total_chunks: 132,
  darglobal_chunks: 62,
  wasalt_chunks: 70,
  categories: {
    projects: 70,
    company_profile: 11,
    press_releases: 15,
    faqs: 6,
    auctions: 5,
    listings: 15,
    governance: 4,
    licensing: 1,
    brand_partners: 1,
    broker_solutions: 1,
    milestones: 1,
    taxonomy: 1,
    contact: 1,
  },
  primary_documents: ["data/DARGLOBAL_VERIFIED_DATA.md", "data/WASALT_VERIFIED_DATA.md"],
};

describe("/health field bindings", () => {
  it("reads the indexed chunk count from chunks_indexed", () => {
    expect(healthChunks(health)).toBe(132);
  });
  it("reads the model from active_model", () => {
    expect(healthModel(health)).toBe("google/gemma-4-31b-it:free");
  });
  it("reads the vector index and the OpenRouter flag", () => {
    expect(healthVectorStore(health)).toBe("FAISS_IndexFlatIP");
    expect(healthProvider(health)).toBe("OpenRouter");
  });
  it("hides the :free pricing suffix in displayed model names", () => {
    expect(modelLabel(healthModel(health))).toBe("google/gemma-4-31b-it");
    expect(modelLabel("openai/gpt-4o")).toBe("openai/gpt-4o");
    expect(modelLabel(undefined)).toBe("");
  });
});

describe("/sources field bindings", () => {
  it("reports each company's own chunk count", () => {
    expect(companyStats(sources, "DarGlobal")).toEqual({ chunks: 62 });
    expect(companyStats(sources, "Wasalt")).toEqual({ chunks: 70 });
  });
  it("keeps counts hidden while the backend is offline", () => {
    expect(companyStats(null, "DarGlobal")).toBeNull();
    expect(companyStats(null, "Wasalt")).toBeNull();
  });
  it("maps UI category labels onto the payload's category keys", () => {
    expect(sourceCategoryCount(sources, "Projects")).toBe(70);
    expect(sourceCategoryCount(sources, "Company Profile")).toBe(11);
    expect(sourceCategoryCount(sources, "Press Releases")).toBe(15);
    expect(sourceCategoryCount(sources, "FAQs")).toBe(6);
    expect(sourceCategoryCount(sources, "Auctions")).toBe(5);
    expect(sourceCategoryCount(sources, "Property Listings")).toBe(15);
    expect(sourceCategoryCount(sources, "Brand Partnerships")).toBe(1);
    expect(sourceCategoryCount(sources, "Services and Taxonomy")).toBe(1);
    expect(sourceCategoryCount(sources, "Board Members")).toBeUndefined();
  });
});

import { vi } from "vitest";
import { askChatbot, searchKnowledge } from "@/lib/api";
describe("unified search only", () => {
  it.each(["DarGlobal", "Wasalt", "Unified Search"] as const)("sends company all for %s", async (c) => {
    const f = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ answer: "", sources: [] }) });
    vi.stubGlobal("fetch", f);
    await askChatbot("q", c);
    await searchKnowledge("q", c);
    for (const call of f.mock.calls) expect(JSON.parse(call[1].body)).toMatchObject({ company: "all", top_k: 5 });
    vi.unstubAllGlobals();
  });
});

import { streamChatbot } from "@/lib/api";
const sse = (chunks: string[]) =>
  new ReadableStream({
    start(c) {
      for (const x of chunks) c.enqueue(new TextEncoder().encode(x));
      c.close();
    },
  });
describe("streamChatbot", () => {
  it("emits tokens split across chunks then done", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, body: sse([
      'data: {"type":"token","token":"Hel"}\n\ndata: {"type":"tok',
      'en","token":"lo"}\n\ndata: {"type":"done","answer":"Hello","sources":[],"ttft_ms":12}\n\n',
    ]) }));
    const tokens: string[] = []; const done = vi.fn(); const err = vi.fn();
    await streamChatbot("q", "Wasalt", 5, (t) => tokens.push(t), done, err);
    expect(tokens).toEqual(["Hel", "lo"]);
    expect(done.mock.calls[0]?.[0]).toMatchObject({ answer: "Hello", ttft_ms: 12 });
    expect(err).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });
  it("reports a 404 as an error so the caller can fall back", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 404, body: null }));
    const err = vi.fn(); const done = vi.fn();
    await streamChatbot("q", "DarGlobal", 5, () => {}, done, err);
    expect(err).toHaveBeenCalledOnce();
    expect(done).not.toHaveBeenCalled();
    vi.unstubAllGlobals();
  });
  it("reports server error events", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, body: sse(['data: {"type":"error","message":"boom"}\n\n']) }));
    const err = vi.fn();
    await streamChatbot("q", "DarGlobal", 5, () => {}, () => {}, err);
    expect(err.mock.calls[0]?.[0].message).toBe("boom");
    vi.unstubAllGlobals();
  });
});
