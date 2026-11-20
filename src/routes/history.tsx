import { createFileRoute, Link } from "@tanstack/react-router";
import { MessageSquare, ArrowUpRight } from "lucide-react";
import { AppShell } from "@/components/assistant/shell";
import { useAssistant } from "@/components/assistant/context";
import { Button } from "@/components/ui/button";
export const Route = createFileRoute("/history")({
  head: () => ({
    meta: [
      { title: "Conversation History | DarGlobal × Wasalt AI" },
      {
        name: "description",
        content: "Return to real estate conversations from your current demo session.",
      },
      { property: "og:title", content: "Conversation History | DarGlobal × Wasalt AI" },
      { property: "og:description", content: "Your real estate insights, together." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Page,
});
function Page() {
  const a = useAssistant();
  return (
    <AppShell>
      <main className="content-page">
        <div className="page-eyebrow">YOUR WORKSPACE</div>
        <h1>Conversation history</h1>
        <p className="page-intro">
          Your real estate insights, all in one place. Current session only.
        </p>
        {a.threads.length ? (
          a.threads.map((t) => (
            <Link
              key={t.id}
              to="/chat/$threadId"
              params={{ threadId: t.id }}
              className="history-row"
            >
              <MessageSquare />
              <div>
                <strong>{t.title}</strong>
                <span>
                  {t.company} · {t.messages.length} messages
                </span>
              </div>
              <ArrowUpRight />
            </Link>
          ))
        ) : (
          <div className="empty-history">
            <MessageSquare size={36} />
            <h2>A fresh perspective starts with a question.</h2>
            <Button asChild variant="gold">
              <Link to="/">
                Start a conversation
                <ArrowUpRight />
              </Link>
            </Button>
          </div>
        )}
      </main>
    </AppShell>
  );
}
