import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { checkBackendHealth, getApiBaseUrl, setApiBaseUrl, type HealthResponse } from "@/lib/api";
import type { ChatItem, Company, Thread } from "./data";

export const THREADS_STORAGE_KEY = "darglobal_wasalt_threads";
export const COMPANY_STORAGE_KEY = "darglobal_wasalt_company";
export const THEME_STORAGE_KEY = "darglobal_wasalt_theme";

const COMPANIES: Company[] = ["DarGlobal", "Wasalt", "Unified Search"];
const DEFAULT_COMPANY: Company = "Unified Search";
const DEFAULT_THEME = "Ivory";
const EMPTY_THREADS: Thread[] = [];

// localStorage only exists in the browser and can throw (private mode, quota,
// blocked storage), so every access is guarded and falls back to the default.
const canStore = () => {
  try {
    return typeof window !== "undefined" && !!window.localStorage;
  } catch {
    return false;
  }
};

const readStorage = (key: string) => {
  try {
    return canStore() ? window.localStorage.getItem(key) : null;
  } catch {
    return null;
  }
};

const writeStorage = (key: string, value: string) => {
  try {
    if (canStore()) window.localStorage.setItem(key, value);
  } catch {
    /* storage blocked: the session stays in memory only */
  }
};

const removeStorage = (key: string) => {
  try {
    if (canStore()) window.localStorage.removeItem(key);
  } catch {
    /* storage blocked: nothing to remove */
  }
};

const readJSON = <T,>(key: string, fallback: T): T => {
  const raw = readStorage(key);
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
};

const isMessage = (m: unknown): m is ChatItem => {
  if (typeof m !== "object" || m === null) return false;
  const v = m as Record<string, unknown>;
  const parts = v["parts"];
  return (
    typeof v["id"] === "string" &&
    (v["role"] === "user" || v["role"] === "assistant") &&
    Array.isArray(parts) &&
    parts.every(
      (p) =>
        typeof p === "object" && p !== null && typeof (p as { text?: unknown }).text === "string",
    )
  );
};

const isThread = (t: unknown): t is Thread => {
  if (typeof t !== "object" || t === null) return false;
  const v = t as Record<string, unknown>;
  const messages = v["messages"];
  return (
    typeof v["id"] === "string" &&
    typeof v["title"] === "string" &&
    COMPANIES.includes(v["company"] as Company) &&
    Array.isArray(messages) &&
    messages.every(isMessage)
  );
};

const readThreads = (): Thread[] => {
  const parsed = readJSON<unknown>(THREADS_STORAGE_KEY, []);
  return Array.isArray(parsed) ? parsed.filter(isThread) : [];
};

const readCompany = (): Company => {
  const stored = readStorage(COMPANY_STORAGE_KEY);
  return COMPANIES.includes(stored as Company) ? (stored as Company) : DEFAULT_COMPANY;
};

const readTheme = (): string => readStorage(THEME_STORAGE_KEY) ?? DEFAULT_THEME;

const Context = createContext<{
  company: Company;
  setCompany: (c: Company) => void;
  threads: Thread[];
  createThread: (question?: string) => string;
  updateThread: (id: string, update: (t: Thread) => Thread) => void;
  deleteThread: (id: string) => void;
  clearHistory: () => void;
  settings: boolean;
  setSettings: (v: boolean) => void;
  theme: string;
  setTheme: (v: string) => void;
  health: HealthResponse | null;
  online: boolean;
  refreshHealth: () => void;
  backendUrl: string;
  setBackendUrl: (v: string) => void;
} | null>(null);

export function AssistantProvider({ children }: { children: ReactNode }) {
  const [threads, setThreads] = useState<Thread[]>(readThreads);
  const [company, setCompanyState] = useState<Company>(readCompany);
  const [settings, setSettings] = useState(false);
  const [theme, setThemeState] = useState<string>(readTheme);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [online, setOnline] = useState(false);
  const [backendUrl, setUrl] = useState(getApiBaseUrl());
  // The server always renders the defaults, so the stored values are swapped in
  // only after hydration — that keeps the first client paint identical to the
  // server markup instead of mismatching it.
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => setHydrated(true), []);
  const refreshHealth = useCallback(() => {
    checkBackendHealth()
      .then((h) => {
        setHealth(h);
        setOnline(true);
      })
      .catch(() => setOnline(false));
  }, []);
  useEffect(() => {
    refreshHealth();
    const id = setInterval(refreshHealth, 15000);
    return () => clearInterval(id);
  }, [refreshHealth, backendUrl]);
  useEffect(() => {
    // An empty history is stored as "no key", so clearing really removes it.
    if (threads.length) writeStorage(THREADS_STORAGE_KEY, JSON.stringify(threads));
    else removeStorage(THREADS_STORAGE_KEY);
  }, [threads]);
  const setBackendUrl = (v: string) => {
    setApiBaseUrl(v);
    setUrl(getApiBaseUrl());
  };
  const setCompany = useCallback((c: Company) => {
    setCompanyState(c);
    writeStorage(COMPANY_STORAGE_KEY, c);
  }, []);
  const setTheme = useCallback((v: string) => {
    setThemeState(v);
    writeStorage(THEME_STORAGE_KEY, v);
  }, []);
  const clearHistory = useCallback(() => {
    removeStorage(THREADS_STORAGE_KEY);
    setThreads([]);
  }, []);
  const deleteThread = useCallback((id: string) => {
    setThreads((p) => {
      const next = p.filter((t) => t.id !== id);
      if (next.length) writeStorage(THREADS_STORAGE_KEY, JSON.stringify(next));
      else removeStorage(THREADS_STORAGE_KEY);
      return next;
    });
  }, []);
  const createThread = (question?: string) => {
    const id = crypto.randomUUID();
    setThreads((p) => [
      {
        id,
        title: question || "New conversation",
        company,
        messages: question
          ? [{ id: crypto.randomUUID(), role: "user", parts: [{ type: "text", text: question }] }]
          : [],
      },
      ...p,
    ]);
    return id;
  };
  return (
    <Context.Provider
      value={{
        company: hydrated ? company : DEFAULT_COMPANY,
        setCompany,
        threads: hydrated ? threads : EMPTY_THREADS,
        createThread,
        updateThread: (id, update) =>
          setThreads((p) => p.map((t) => (t.id === id ? update(t) : t))),
        deleteThread,
        clearHistory,
        settings,
        setSettings,
        theme: hydrated ? theme : DEFAULT_THEME,
        setTheme,
        health,
        online,
        refreshHealth,
        backendUrl,
        setBackendUrl,
      }}
    >
      {children}
    </Context.Provider>
  );
}
export function useAssistant() {
  const value = useContext(Context);
  if (!value) throw new Error("Assistant provider missing");
  return value;
}
