import { createFileRoute } from "@tanstack/react-router";
import { AppShell, KnowledgeSources } from "@/components/assistant/shell";
export const Route = createFileRoute("/sources")({
  head: () => ({
    meta: [
      { title: "Knowledge Sources | DarGlobal × Wasalt AI" },
      {
        name: "description",
        content: "Browse DarGlobal and Wasalt sample knowledge collections and source categories.",
      },
      { property: "og:title", content: "Knowledge Sources | DarGlobal × Wasalt AI" },
      {
        property: "og:description",
        content: "Two real estate collections in one knowledge library.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: () => (
    <AppShell>
      <KnowledgeSources />
    </AppShell>
  ),
});
