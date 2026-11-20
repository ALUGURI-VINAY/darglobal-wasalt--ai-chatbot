import { useEffect, useState, type ReactNode } from "react";
import {
  fetchKnowledgeSources,
  healthChunks,
  healthModel,
  healthProvider,
  healthVectorStore,
  modelLabel,
  sourceCategoryCount,
  type SourcesResponse,
} from "@/lib/api";
import { Link, useLocation, useNavigate } from "@tanstack/react-router";
import {
  Plus,
  MessageSquare,
  History,
  Library,
  Info,
  Settings,
  PanelLeftClose,
  PanelLeftOpen,
  ArrowUpRight,
  ChevronDown,
  X,
  Menu,
  ShieldCheck,
  Globe,
  Building2,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { useAssistant } from "./context";
import { collections, type Company } from "./data";
export function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <div className="brand">
      <span className="brand-mark" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
      {!compact && (
        <div>
          <div className="brand-names">
            DarGlobal <span>×</span> Wasalt<span className="ai-tag">AI</span>
          </div>
          <div className="brand-subtitle">INTELLIGENT REAL ESTATE</div>
        </div>
      )}
    </div>
  );
}
export function ConnectionStatus() {
  const a = useAssistant();
  const chunks = healthChunks(a.health);
  return (
    <span className="connection" title={a.backendUrl}>
      <span style={a.online ? { background: "var(--success)" } : undefined} />
      {a.online
        ? `Connected${chunks !== undefined ? ` (${chunks} Chunks)` : ""}`
        : `Connecting to backend (${a.backendUrl})`}
    </span>
  );
}
export function AppShell({ children }: { children: ReactNode }) {
  const a = useAssistant();
  const navigate = useNavigate();
  const path = useLocation().pathname;
  const [collapsed, setCollapsed] = useState(false);
  const [mobile, setMobile] = useState(false);
  const nav = [
    { to: "/", label: "AI Assistant", icon: MessageSquare },
    { to: "/history", label: "Conversation History", icon: History },
    { to: "/sources", label: "Knowledge Sources", icon: Library },
    { to: "/about", label: "About Assistant", icon: Info },
  ] as const;
  return (
    <div
      className={`app-shell ${collapsed ? "sidebar-collapsed" : ""} ${a.theme === "Charcoal" ? "workspace-dark" : ""}`}
    >
      {mobile && <div className="mobile-scrim" onClick={() => setMobile(false)} />}
      <aside className={`app-sidebar ${mobile ? "mobile-open" : ""}`}>
        <div className="sidebar-brand">
          <Brand compact={collapsed} />
          <Button
            variant="nav"
            size="icon-sm"
            aria-label="Close navigation"
            className="mobile-close"
            onClick={() => setMobile(false)}
          >
            <X />
          </Button>
        </div>
        <Button
          variant="gold"
          className="new-chat"
          onClick={() => {
            setMobile(false);
            navigate({ to: "/" });
          }}
        >
          <Plus />
          {!collapsed && "New conversation"}
        </Button>
        <div className="nav-label">{!collapsed && "WORKSPACE"}</div>
        <nav>
          {nav.map((n) => (
            <Button
              asChild
              variant="nav"
              key={n.to}
              className={`nav-item ${path === n.to || (n.to === "/" && path.startsWith("/chat/")) ? "nav-active" : ""}`}
              title={n.label}
            >
              <Link to={n.to} onClick={() => setMobile(false)}>
                <n.icon />
                {!collapsed && <span>{n.label}</span>}
                {!collapsed && n.to === "/" && <span className="nav-dot" />}
              </Link>
            </Button>
          ))}
        </nav>
        {!collapsed && (
          <div className="recent">
            <div className="nav-label">
              RECENT CONVERSATIONS <span>{a.threads.length}</span>
            </div>
            {a.threads.length ? (
              a.threads.slice(0, 5).map((t) => (
                <Link
                  key={t.id}
                  to="/chat/$threadId"
                  params={{ threadId: t.id }}
                  className="recent-thread"
                  onClick={() => setMobile(false)}
                >
                  <MessageSquare size={14} />
                  <span>{t.title}</span>
                </Link>
              ))
            ) : (
              <p className="empty-recent">Your conversations will appear here.</p>
            )}
          </div>
        )}
        <div className="sidebar-bottom">
          {!collapsed && (
            <div className="workspace-note">
              <ShieldCheck size={18} />
              <div>
                Grounded in your knowledge<div>Two brands. One trusted perspective.</div>
              </div>
            </div>
          )}
          <Button
            variant="nav"
            className="nav-item"
            title="Settings"
            onClick={() => a.setSettings(true)}
          >
            <Settings />
            {!collapsed && "Settings"}
          </Button>
          <div className="sidebar-footer">
            {!collapsed && (
              <span>
                DarGlobal × Wasalt <span>v1.0</span>
              </span>
            )}
            <Button
              variant="nav"
              size="icon-sm"
              aria-label="Collapse sidebar"
              onClick={() => setCollapsed(!collapsed)}
            >
              {collapsed ? <PanelLeftOpen /> : <PanelLeftClose />}
            </Button>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="top-header">
          <div className="header-title">
            <Button
              variant="ghost"
              size="icon"
              className="mobile-menu"
              aria-label="Open navigation"
              onClick={() => setMobile(true)}
            >
              <Menu />
            </Button>
            <span>Intelligent Real Estate Assistant</span>
            <span className="header-divider" />
            <span className="header-company">
              {a.company}
              <ChevronDown size={12} />
            </span>
          </div>
          <div className="header-right">
            <ConnectionStatus />
            <span className="model-label">
              LLM · {a.online ? modelLabel(healthModel(a.health)) : "Not connected"}
            </span>
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label="Open settings"
              title="Settings"
              onClick={() => a.setSettings(true)}
            >
              <Settings size={17} />
            </Button>
            <div className="user-avatar" title="Guest workspace">
              JD
            </div>
          </div>
        </header>
        {children}
        <footer className="workspace-footer">
          <span>
            <ShieldCheck size={12} /> Knowledge-led. Source-backed.
          </span>
          <span>DarGlobal × Wasalt · Intelligent Real Estate</span>
        </footer>
      </div>
      <SettingsModal />
    </div>
  );
}
export function CompanySelector() {
  const a = useAssistant();
  const items: { name: Company; desc: string; icon: typeof Building2 }[] = [
    { name: "Unified Search", desc: "One search. Both knowledge bases.", icon: Globe },
  ];
  return (
    <div className="company-selector">
      {items.map((c) => (
        <Button
          key={c.name}
          variant="choice"
          aria-pressed={a.company === c.name}
          className={`company-choice ${a.company === c.name ? "selected" : ""}`}
          onClick={() => a.setCompany(c.name)}
        >
          <span className={`company-icon ${c.name === "Wasalt" ? "wasalt" : ""}`}>
            <c.icon />
          </span>
          <span className="company-copy">
            <strong>{c.name}</strong>
            <span>{c.desc}</span>
          </span>
          <span className="choice-radio">{a.company === c.name && <Check size={10} />}</span>
        </Button>
      ))}
    </div>
  );
}
export function SettingsModal() {
  const a = useAssistant();
  const [url, setUrl] = useState(a.backendUrl);
  useEffect(() => setUrl(a.backendUrl), [a.backendUrl]);
  return (
    <Dialog open={a.settings} onOpenChange={a.setSettings}>
      <DialogContent className="settings-dialog">
        <DialogHeader>
          <DialogTitle>Workspace settings</DialogTitle>
          <DialogDescription>DarGlobal × Wasalt assistant configuration</DialogDescription>
        </DialogHeader>
        <div className="settings-row">
          <span>AI provider</span>
          <strong>{healthProvider(a.health)}</strong>
        </div>
        <div className="settings-row">
          <span>Selected LLM model</span>
          <strong>{modelLabel(healthModel(a.health))}</strong>
        </div>
        <div className="settings-row">
          <span>Vector store</span>
          <strong>{healthVectorStore(a.health)}</strong>
        </div>
        <div className="settings-row">
          <span>Backend connection</span>
          <strong className={a.online ? undefined : "text-muted-foreground"}>
            {a.online
              ? `Connected${healthChunks(a.health) !== undefined ? ` · ${healthChunks(a.health)} chunks` : ""}`
              : "Disconnected"}
          </strong>
        </div>
        <form
          className="settings-row"
          onSubmit={(e) => {
            e.preventDefault();
            a.setBackendUrl(url);
          }}
        >
          <span>Backend URL</span>
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onBlur={() => a.setBackendUrl(url)}
            aria-label="Backend URL"
            className="rounded-md border border-input bg-transparent px-2 py-1 text-sm"
          />
        </form>
        <div className="settings-row">
          <span>Appearance</span>
          <div className="theme-choices">
            {["Ivory", "Charcoal"].map((t) => (
              <Button
                key={t}
                variant={a.theme === t ? "default" : "outline"}
                size="sm"
                onClick={() => a.setTheme(t)}
              >
                {t}
              </Button>
            ))}
          </div>
        </div>
        <div className="settings-row">
          <span>Conversation storage</span>
          <strong>This session only</strong>
        </div>
        <Button
          variant="outline"
          onClick={() => {
            if (window.confirm("Clear all conversations in this session?")) {
              a.clearHistory();
              a.setSettings(false);
            }
          }}
        >
          Clear conversation history
        </Button>
      </DialogContent>
    </Dialog>
  );
}
export function companyStats(data: SourcesResponse | null, company: string) {
  // No response yet: keep the collection marked "Index pending" rather than
  // presenting the built-in counts as live.
  if (!data) return null;
  const key = company.toLowerCase();
  if (key === "darglobal") return { chunks: data.darglobal_chunks ?? 62 };
  if (key === "wasalt") return { chunks: data.wasalt_chunks ?? 70 };
  return null;
}
export function KnowledgeSources() {
  const a = useAssistant();
  const [data, setData] = useState<SourcesResponse | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    fetchKnowledgeSources()
      .then((d) => {
        setData(d);
        setFailed(false);
      })
      .catch(() => setFailed(true));
  }, [a.backendUrl, a.online]);
  return (
    <div className="content-page">
      <div className="page-eyebrow">THE KNOWLEDGE LIBRARY</div>
      <h1>Two collections. A world of insight.</h1>
      <p className="page-intro">
        Explore the knowledge behind your real estate assistant.
        {data?.total_chunks !== undefined && ` ${data.total_chunks} indexed chunks in total.`}
        {failed && " Live index details are unavailable while the backend is offline."}
      </p>
      <div className="source-collections">
        {collections.map((c) => {
          const stats = companyStats(data, c.company);
          const categories: [string, number | undefined][] = c.categories.map((x) => [
            x,
            sourceCategoryCount(data, x),
          ]);
          return (
            <section key={c.company}>
              <div className="collection-head">
                <span className="company-icon">
                  <Building2 />
                </span>
                <div>
                  <h2>{c.company}</h2>
                  <p>{c.description}</p>
                </div>
                <span className="sample-tag">
                  {stats?.chunks !== undefined ? `${stats.chunks} chunks` : "Index pending"}
                </span>
              </div>
              {categories.map(([category, count]) => (
                <div className="document-row" key={category}>
                  <Library size={18} />
                  <div>
                    <strong>{category}</strong>
                    <span>
                      {c.company} ·{" "}
                      {count !== undefined
                        ? `${count} indexed chunks`
                        : stats
                          ? "Indexed"
                          : "Index details unavailable"}
                    </span>
                  </div>
                  <Button
                    asChild
                    variant="ghost"
                    size="icon-sm"
                    title={`Open ${c.company} official website`}
                  >
                    <a href={c.url} target="_blank" rel="noreferrer">
                      <ArrowUpRight />
                    </a>
                  </Button>
                </div>
              ))}
              <p className="collection-note">
                Official homepage references ·{" "}
                {stats ? "Live index connected" : "Live index unavailable"}
              </p>
            </section>
          );
        })}
      </div>
    </div>
  );
}
