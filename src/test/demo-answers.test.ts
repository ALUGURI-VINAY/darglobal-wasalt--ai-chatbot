import { describe, expect, it } from "vitest";
import { collections, demoAnswer } from "@/components/assistant/data";
describe("Frontend demonstration boundaries", () => {
  it("does not fabricate a REGA license number", () => {
    const answer = demoAnswer("What is Wasalt's REGA license number?", "Wasalt");
    expect(answer.text).toContain("does not contain a verified REGA license number");
    expect(answer.text).not.toMatch(/\b\d{6,}\b/);
  });
  it("keeps indexed record counts unavailable rather than inventing them", () => {
    for (const collection of collections) expect(collection).not.toHaveProperty("recordCount");
  });
});
import { mapCompany } from "@/lib/api";
describe("Backend company mapping", () => {
  it("maps DarGlobal to darglobal", () => expect(mapCompany("DarGlobal")).toBe("darglobal"));
  it("maps Wasalt to wasalt", () => expect(mapCompany("Wasalt")).toBe("wasalt"));
  it("maps Unified Search to all", () => expect(mapCompany("Unified Search")).toBe("all"));
});
