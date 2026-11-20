import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/assistant/shell";
import { WelcomeScreen } from "@/components/assistant/chat";
export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "DarGlobal × Wasalt | Intelligent Real Estate Assistant" },
      {
        name: "description",
        content:
          "Explore luxury developments, property insights and two real estate knowledge collections.",
      },
      { property: "og:title", content: "DarGlobal × Wasalt | Intelligent Real Estate Assistant" },
      { property: "og:description", content: "Your real estate knowledge, reimagined." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: () => (
    <AppShell>
      <WelcomeScreen />
    </AppShell>
  ),
});
