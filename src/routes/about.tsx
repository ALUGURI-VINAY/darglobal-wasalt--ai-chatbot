import { createFileRoute } from "@tanstack/react-router";
import { Building2, Library, ShieldCheck } from "lucide-react";
import { AppShell } from "@/components/assistant/shell";
export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "About the Assistant | DarGlobal × Wasalt AI" },
      {
        name: "description",
        content: "Learn about the DarGlobal and Wasalt real estate knowledge assistant prototype.",
      },
      { property: "og:title", content: "About the Assistant | DarGlobal × Wasalt AI" },
      { property: "og:description", content: "A considered perspective on real estate knowledge." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: () => (
    <AppShell>
      <main className="content-page about-page">
        <div className="page-eyebrow">A CONSIDERED PERSPECTIVE</div>
        <h1>
          Real estate knowledge.
          <br />
          Intelligently connected.
        </h1>
        <p className="page-intro">
          DarGlobal × Wasalt brings two distinct real estate perspectives into one focused
          workspace.
        </p>
        <div className="about-features">
          <section>
            <Building2 />
            <h2>DarGlobal</h2>
            <p>
              Luxury developments, company information, leadership, partnerships and press releases.
            </p>
          </section>
          <section>
            <Library />
            <h2>Wasalt</h2>
            <p>Property listings, auctions, services, projects and platform information.</p>
          </section>
          <section>
            <ShieldCheck />
            <h2>A transparent perspective</h2>
            <p>
              This frontend prototype uses clearly labeled sample answers and homepage references.
              No live backend or verified document index is connected.
            </p>
          </section>
        </div>
      </main>
    </AppShell>
  ),
});
