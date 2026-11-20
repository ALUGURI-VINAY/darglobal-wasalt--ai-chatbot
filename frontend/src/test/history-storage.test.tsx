import { fireEvent, render, screen, waitFor, act } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import {
  AssistantProvider,
  COMPANY_STORAGE_KEY,
  THEME_STORAGE_KEY,
  THREADS_STORAGE_KEY,
  useAssistant,
} from "@/components/assistant/context";

// Small harness: exposes the provider's state and the actions the UI calls.
function Harness() {
  const a = useAssistant();
  return (
    <div>
      <span data-testid="threads">{a.threads.length}</span>
      <span data-testid="titles">{a.threads.map((t) => t.title).join("|")}</span>
      <span data-testid="company">{a.company}</span>
      <span data-testid="theme">{a.theme}</span>
      <button onClick={() => a.createThread("What is Wasalt?")}>New</button>
      <button onClick={() => a.setCompany("Wasalt")}>Wasalt</button>
      <button onClick={() => a.setTheme("Charcoal")}>Charcoal</button>
      <button onClick={() => a.clearHistory()}>Clear</button>
      <button onClick={() => a.threads[0] && a.deleteThread(a.threads[0].id)}>DeleteFirst</button>
    </div>
  );
}

const renderProvider = () =>
  render(
    <AssistantProvider>
      <Harness />
    </AssistantProvider>,
  );

const stored = (key: string) => window.localStorage.getItem(key);
const click = (label: string) => fireEvent.click(screen.getByText(label));

describe("localStorage persistence", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("saves a conversation under the threads key", async () => {
    renderProvider();
    click("New");

    await waitFor(() => expect(stored(THREADS_STORAGE_KEY)).toBeTruthy());
    const saved = JSON.parse(stored(THREADS_STORAGE_KEY) || "[]");
    expect(saved).toHaveLength(1);
    expect(saved[0].title).toBe("What is Wasalt?");
    expect(saved[0].company).toBe("Unified Search");
    expect(saved[0].messages[0].parts[0].text).toBe("What is Wasalt?");
  });

  it("restores conversations, company and theme on the next visit", async () => {
    const first = renderProvider();
    click("New");
    click("Wasalt");
    click("Charcoal");
    await waitFor(() => expect(stored(THEME_STORAGE_KEY)).toBe("Charcoal"));

    first.unmount();
    renderProvider();

    await waitFor(() => expect(screen.getByTestId("threads")).toHaveTextContent("1"));
    expect(screen.getByTestId("titles")).toHaveTextContent("What is Wasalt?");
    expect(screen.getByTestId("company")).toHaveTextContent("Wasalt");
    expect(screen.getByTestId("theme")).toHaveTextContent("Charcoal");
  });

  it("removes the stored threads when history is cleared", async () => {
    renderProvider();
    click("New");
    await waitFor(() => expect(stored(THREADS_STORAGE_KEY)).toBeTruthy());

    click("Clear");

    await waitFor(() => expect(stored(THREADS_STORAGE_KEY)).toBeNull());
    expect(screen.getByTestId("threads")).toHaveTextContent("0");
  });

  it("falls back to defaults when stored data is unreadable", async () => {
    window.localStorage.setItem(THREADS_STORAGE_KEY, "{not json");
    window.localStorage.setItem(COMPANY_STORAGE_KEY, "Acme Corp");
    window.localStorage.setItem(THEME_STORAGE_KEY, "Sepia");

    renderProvider();

    await waitFor(() => expect(screen.getByTestId("threads")).toHaveTextContent("0"));
    expect(screen.getByTestId("company")).toHaveTextContent("Unified Search");
    expect(screen.getByTestId("theme")).toHaveTextContent("Sepia");
  });

  it("drops stored entries that are not conversations", async () => {
    window.localStorage.setItem(
      THREADS_STORAGE_KEY,
      JSON.stringify([
        { id: "a", title: "Keep", company: "Wasalt", messages: [] },
        { id: "b", title: "Broken", company: "Wasalt" },
        "nope",
        null,
      ]),
    );

    renderProvider();

    await waitFor(() => expect(screen.getByTestId("threads")).toHaveTextContent("1"));
    expect(screen.getByTestId("titles")).toHaveTextContent("Keep");
  });

  it("writes the current threads back to storage without user input", async () => {
    window.localStorage.setItem(
      THREADS_STORAGE_KEY,
      JSON.stringify([{ id: "a", title: "Keep", company: "Wasalt", messages: [] }]),
    );

    renderProvider();
    await waitFor(() => expect(screen.getByTestId("threads")).toHaveTextContent("1"));
    await act(async () => {
      await Promise.resolve();
    });

    expect(JSON.parse(stored(THREADS_STORAGE_KEY) || "[]")).toEqual([
      { id: "a", title: "Keep", company: "Wasalt", messages: [] },
    ]);
  });

  it("deletes a single thread with deleteThread", async () => {
    renderProvider();
    click("New");
    await waitFor(() => expect(screen.getByTestId("threads")).toHaveTextContent("1"));
    click("DeleteFirst");
    await waitFor(() => expect(screen.getByTestId("threads")).toHaveTextContent("0"));
  });
});
