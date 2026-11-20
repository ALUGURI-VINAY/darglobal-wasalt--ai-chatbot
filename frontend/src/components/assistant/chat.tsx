import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import {
  ArrowUpRight,
  ArrowUp,
  Building2,
  Globe,
  Users,
  Gem,
  ChevronDown,
  ExternalLink,
  Copy,
  RotateCcw,
  ThumbsUp,
  ThumbsDown,
  Check,
  Trash2,
  ShieldCheck,
  ArrowRight,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  Message,
  MessageContent,
  MessageResponse,
  MessageActions,
  MessageAction,
} from "@/components/ai-elements/message";
import {
  PromptInput,
  PromptInputTextarea,
  PromptInputFooter,
  PromptInputSubmit,
} from "@/components/ai-elements/prompt-input";
import { Shimmer } from "@/components/ai-elements/shimmer";
import villa from "@/assets/luxury-villa.asset.json";
import { useAssistant } from "./context";
import { Brand, CompanySelector } from "./shell";
import { askChatbot, healthModel, modelLabel, streamChatbot, type ChatResponse } from "@/lib/api";
import { suggestions, type Source, type ChatItem } from "./data";
export function SourcePanel({ sources }: { sources: Source[] }) {
  return (
    <details className="source-panel">
      <summary>
        <LibraryIcon /> Sources ({sources.length})<span>Retrieved references</span>
        <ChevronDown size={14} />
      </summary>
      <div className="citation-grid">
        {sources.map((s, i) => (
          <article className="citation" key={`${s.title}-${i}`}>
            <div className="citation-heading">
              <span>{i + 1}</span>
              <strong>{s.title}</strong>
            </div>
            <p>
              {s.company} · {s.category}
              {typeof s.score === "number" ? ` · ${(s.score * 100).toFixed(0)}% match` : ""}
            </p>
            {s.snippet && <p>{s.snippet}</p>}
            {s.url && (
              <>
                <a href={s.url} target="_blank" rel="noreferrer">
                  View original source <ExternalLink size={12} />
                </a>
                <small>{s.url}</small>
              </>
            )}
          </article>
        ))}
      </div>
    </details>
  );
}
function LibraryIcon() {
  return <Building2 size={14} />;
}
export function ChatMessage({
  message,
  regenerate,
}: {
  message: ChatItem;
  regenerate: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<string>();
  return (
    <Message from={message.role} className="chat-message">
      {message.role === "assistant" && (
        <div className="assistant-byline">
          <Brand compact />
          <strong>Real Estate Assistant</strong>
          <span>{message.error ? "CONNECTION ISSUE" : modelLabel(message.model) || "HYBRID RAG"}</span>
        </div>
      )}
      <MessageContent className={message.role === "user" ? "user-content" : "assistant-content"}>
        {message.parts.map((p, i) => (
          <MessageResponse key={i}>{p.text}</MessageResponse>
        ))}
      </MessageContent>
      {message.error && (
        <Button variant="outline" size="sm" onClick={regenerate}>
          <RotateCcw /> Try again
        </Button>
      )}
      {message.sources && message.sources.length > 0 && <SourcePanel sources={message.sources} />}{" "}
      {message.role === "assistant" && (
        <MessageActions className="response-actions">
          <MessageAction
            tooltip={copied ? "Copied" : "Copy response"}
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(message.parts.map((p) => p.text).join("\n"));
                setCopied(true);
              } catch {
                toast.error("Unable to copy. Please select the response text.");
              }
            }}
          >
            {copied ? <Check /> : <Copy />}
          </MessageAction>
          <MessageAction tooltip="Regenerate response" onClick={regenerate}>
            <RotateCcw />
          </MessageAction>
          <MessageAction
            tooltip="Helpful"
            aria-pressed={feedback === "positive"}
            onClick={() => {
              setFeedback("positive");
              toast.success("Feedback noted for this session");
            }}
          >
            <ThumbsUp />
          </MessageAction>
          <MessageAction
            tooltip="Not helpful"
            aria-pressed={feedback === "negative"}
            onClick={() => {
              setFeedback("negative");
              toast.success("Feedback noted for this session");
            }}
          >
            <ThumbsDown />
          </MessageAction>
        </MessageActions>
      )}
    </Message>
  );
}
export function ChatInput({
  send,
  busy,
  stop,
  company,
}: {
  send: (text: string) => void;
  busy: boolean;
  stop: () => void;
  company: string;
}) {
  const [value, setValue] = useState("");
  const { online } = useAssistant();
  const ref = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    if (!busy) ref.current?.focus();
  }, [busy]);
  return (
    <div className="composer-wrap">
      <PromptInput
        className="chat-composer"
        onSubmit={({ text }) => {
          if (!text.trim() || busy) return;
          send(text.trim());
          setValue("");
          ref.current?.focus();
        }}
      >
        <PromptInputTextarea
          ref={ref}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Ask anything about real estate…"
          aria-label="Ask a real estate question"
          autoFocus
        />
        <PromptInputFooter>
          <div className="composer-context">
            <span className="small-gold-dot" />
            <span>{company}</span>
            <span className="composer-separator" />
            <span className="demo-inline">{online ? "Live RAG" : "Backend offline"}</span>
          </div>
          <PromptInputSubmit
            status={busy ? "streaming" : "ready"}
            disabled={!busy && !value.trim()}
            onStop={stop}
            className="send-button"
            title={busy ? "Stop response" : "Send message"}
          >
            {!busy && <ArrowUp size={19} />}
          </PromptInputSubmit>
        </PromptInputFooter>
      </PromptInput>
      <p className="composer-disclaimer">
        <ShieldCheck size={12} /> Answers are grounded in the knowledge base. Verify details with
        original sources.
      </p>
    </div>
  );
}
export function WelcomeScreen() {
  const a = useAssistant();
  const navigate = useNavigate();
  const send = (q: string) => {
    const id = a.createThread(q);
    navigate({ to: "/chat/$threadId", params: { threadId: id } });
  };
  const icons = [Building2, Globe, Users, Gem];
  return (
    <main className="welcome-main">
      <div className="welcome-content">
        <div className="welcome-title-row">
          <div className="page-eyebrow">
            <span /> YOUR INTELLIGENT REAL ESTATE PARTNER
          </div>
          <span className="powered-label">Curated knowledge. Considered answers.</span>
        </div>
        <div className="welcome-hero">
          <img
            src={villa.url}
            alt="Contemporary waterfront villa overlooking an infinity pool and the Dubai skyline"
          />
          <div className="hero-shade" />
          <div className="hero-copy">
            <span className="hero-eyebrow">EXCEPTIONAL REAL ESTATE. INTELLIGENT INSIGHT.</span>
            <h1>
              Your Real Estate Knowledge,
              <br />
              <em>Reimagined.</em>
            </h1>
            <p>
              Explore luxury developments, property insights and real estate
              <br className="desktop-break" /> information through an intelligent AI assistant.
            </p>
          </div>
          <span className="hero-caption">
            <span /> A NEW PERSPECTIVE ON REAL ESTATE
          </span>
          <span className="hero-image-label">Architectural illustration</span>
        </div>
        <div className="section-heading">
          <h2>Choose your knowledge base</h2>
          <span>A focused search starts here</span>
        </div>
        <CompanySelector />
        <div className="section-heading questions-heading">
          <h2>A little inspiration to get started</h2>
          <span>
            Explore {a.company === "Unified Search" ? "both collections" : a.company}
            <ArrowUpRight size={13} />
          </span>
        </div>
        <div className="suggestion-grid">
          {suggestions[a.company].map((s, i) => {
            const Icon = icons[i % icons.length] ?? Building2;
            return (
              <Button
                variant="choice"
                className="suggestion-card"
                key={s.title}
                onClick={() => send(s.question)}
              >
                <span className="suggestion-icon">
                  <Icon size={19} />
                </span>
                <strong>{s.title}</strong>
                <span>{s.detail}</span>
                <ArrowUpRight className="suggestion-arrow" size={16} />
              </Button>
            );
          })}
        </div>
        <ChatInput company={a.company} send={send} busy={false} stop={() => {}} />
      </div>
    </main>
  );
}
export function ChatWindow({ threadId }: { threadId: string }) {
  const a = useAssistant();
  const thread = a.threads.find((t) => t.id === threadId);
  const [busy, setBusy] = useState(false);
  const pending = useRef<AbortController | undefined>(undefined);
  const navigate = useNavigate();
  const stop = () => {
    pending.current?.abort();
    pending.current = undefined;
    setBusy(false);
  };
  useEffect(
    () => () => {
      pending.current?.abort();
      pending.current = undefined;
    },
    [],
  );
  const respond = useCallback(
    (question: string) => {
      if (!thread || pending.current) return;
      const ctrl = new AbortController();
      pending.current = ctrl;
      setBusy(true);
      const assistantMsgId = crypto.randomUUID();
      let accumulatedText = "";
      let tokenReceived = false;
      const upsert = (patch: Partial<ChatItem>) =>
        a.updateThread(threadId, (t) => {
          const exists = t.messages.some((m) => m.id === assistantMsgId);
          const messages = exists
            ? t.messages.map((m) => (m.id === assistantMsgId ? { ...m, ...patch } : m))
            : [...t.messages, { id: assistantMsgId, role: "assistant" as const, parts: [], ...patch }];
          return { ...t, messages };
        });
      const finish = () => {
        if (pending.current === ctrl) {
          pending.current = undefined;
          setBusy(false);
        }
      };
      const mapSources = (res: ChatResponse) =>
        (res.sources || []).map((s) => ({
          title: s.title || s.chunk_id || "Untitled source",
          company: s.company || "",
          category: s.category || "",
          url: s.source_url || "",
          snippet: s.content_snippet,
          score: s.relevance_score,
        }));
      const complete = (res: ChatResponse, fallbackText = "") =>
        upsert({
          error: false,
          model: (res.model_used as string) || (res.model as string) || healthModel(a.health),
          parts: [{ type: "text", text: res.answer || fallbackText || "No answer was returned." }],
          sources: mapSources(res),
        });
      const showError = (e: unknown) =>
        upsert({
          error: true,
          parts: [
            {
              type: "text",
              text: `### We couldn’t reach the assistant\n\n${e instanceof Error && e.message && !/fetch|network|abort/i.test(e.message) ? e.message : `The knowledge service at ${a.backendUrl} isn’t responding right now.`} Please try again in a moment.`,
            },
          ],
        });
      void streamChatbot(
        question,
        thread.company,
        5,
        (token) => {
          if (ctrl.signal.aborted) return;
          tokenReceived = true;
          accumulatedText += token;
          upsert({ parts: [{ type: "text", text: accumulatedText }] });
        },
        (done) => {
          if (ctrl.signal.aborted) return;
          complete(done, accumulatedText);
          finish();
        },
        (err) => {
          if (ctrl.signal.aborted) return;
          if (tokenReceived) {
            upsert({
              parts: [
                {
                  type: "text",
                  text: `${accumulatedText}\n\n_The response was interrupted (${err.message}). Use regenerate to try again._`,
                },
              ],
            });
            finish();
            return;
          }
          askChatbot(question, thread.company, 5, ctrl.signal)
            .then((res) => {
              if (!ctrl.signal.aborted) complete(res);
            })
            .catch((e: unknown) => {
              if (!ctrl.signal.aborted) showError(e);
            })
            .finally(finish);
        },
        ctrl.signal,
      );
    },
    [thread, threadId, a],
  );
  useEffect(() => {
    const last = thread?.messages.at(-1);
    if (!last || last.role !== "user" || pending.current) return;
    respond(last.parts[0]?.text || "");
  }, [thread, respond]);
  if (!thread)
    return (
      <main className="content-page">
        <h1>This conversation isn’t available.</h1>
        <p className="page-intro">Conversations are saved in your browser history.</p>
        <Button onClick={() => navigate({ to: "/" })}>
          Start a new conversation
          <ArrowRight />
        </Button>
      </main>
    );
  const send = (q: string) => {
    a.updateThread(threadId, (t) => ({
      ...t,
      title: t.messages.length ? t.title : q,
      messages: [
        ...t.messages,
        { id: crypto.randomUUID(), role: "user", parts: [{ type: "text", text: q }] },
      ],
    }));
    respond(q);
  };
  const regenerate = () => {
    if (busy) return;
    const user = [...thread.messages].reverse().find((m) => m.role === "user");
    if (!user) return;
    a.updateThread(threadId, (t) => ({
      ...t,
      messages: t.messages.at(-1)?.role === "assistant" ? t.messages.slice(0, -1) : t.messages,
    }));
    respond(user.parts[0]?.text || "");
  };
  return (
    <main className="chat-main">
      <div className="chat-topline">
        <div>
          <span className="page-eyebrow">{thread.company.toUpperCase()} KNOWLEDGE</span>
          <h1>{thread.title}</h1>
        </div>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Delete conversation"
          title="Delete conversation"
          onClick={() => {
            if (window.confirm("Delete this conversation?")) {
              stop();
              a.deleteThread(threadId);
              navigate({ to: "/" });
            }
          }}
        >
          <Trash2 />
        </Button>
      </div>
      <Conversation className="transcript">
        <ConversationContent>
          {thread.messages.map((m) => (
            <ChatMessage key={m.id} message={m} regenerate={regenerate} />
          ))}
          {busy && thread.messages.at(-1)?.role === "user" && (
            <Shimmer>Searching the knowledge base…</Shimmer>
          )}
          {!busy && thread.messages.at(-1)?.role === "assistant" && (
            <div className="follow-ups">
              {suggestions[thread.company].slice(0, 2).map((s) => (
                <Button key={s.title} variant="outline" size="sm" onClick={() => send(s.question)}>
                  {s.title}
                  <ArrowUpRight />
                </Button>
              ))}
            </div>
          )}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>
      <ChatInput company={thread.company} send={send} busy={busy} stop={stop} />
    </main>
  );
}
