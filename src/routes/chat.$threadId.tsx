import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/assistant/shell";
import { ChatWindow } from "@/components/assistant/chat";
export const Route = createFileRoute("/chat/$threadId")({
  head: () => ({
    meta: [
      { title: "Conversation | DarGlobal × Wasalt AI" },
      {
        name: "description",
        content: "Explore source-backed sample conversations with the real estate assistant.",
      },
      { property: "og:title", content: "Conversation | DarGlobal × Wasalt AI" },
      { property: "og:description", content: "Your focused real estate knowledge conversation." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Page,
});
function Page() {
  const { threadId } = Route.useParams();
  return (
    <AppShell>
      <ChatWindow key={threadId} threadId={threadId} />
    </AppShell>
  );
}
