import type {
  AIChatResponse,
  AIEnrichResponse,
  AIMessage,
  AIStatus,
  Article,
  ArticleDetail,
  ArticlePage,
  Category,
  ClassificationFlags,
  DashboardStats,
  DuplicateItem,
  EventItem,
  IngestionError,
  IngestionRun,
  KairosState,
  Meta,
  Region,
  Rule,
  Source,
  StrikeFeed,
} from "./types";

const SERVER_API = process.env.API_URL || "http://127.0.0.1:8000";
export const PUBLIC_API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function serverGet<T>(path: string, revalidate = 60): Promise<T | null> {
  try {
    const res = await fetch(`${SERVER_API}${path}`, { next: { revalidate } });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export function buildQuery(params: Record<string, string | number | boolean | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export const api = {
  meta: () => serverGet<Meta>("/api/meta", 300),
  regions: () => serverGet<Region[]>("/api/regions", 600),
  categories: () => serverGet<Meta["categories"]>("/api/categories", 600),
  articles: (params: Record<string, string | number | boolean | undefined> = {}, revalidate = 30) =>
    serverGet<ArticlePage>(`/api/articles${buildQuery(params)}`, revalidate),
  article: (id: number | string) => serverGet<ArticleDetail>(`/api/articles/${id}`, 15),
  lead: () => serverGet<Article | null>("/api/lead", 30),
  breaking: () => serverGet<Article[]>("/api/breaking", 15),
  strikes: (params: Record<string, string | number | boolean | undefined> = {}, revalidate = 30) =>
    serverGet<StrikeFeed>(`/api/strikes${buildQuery(params)}`, revalidate),
  mostRead: () => serverGet<Article[]>("/api/most-read", 60),
  onThisDay: () => serverGet<Article[]>("/api/on-this-day", 300),
  events: () => serverGet<EventItem[]>("/api/events", 30),
  event: (id: number | string) =>
    serverGet<EventItem & { timeline: Article[] }>(`/api/events/${id}`, 20),
  kairos: (limit = 6) => serverGet<Article[]>(`/api/kairos?limit=${limit}`, 30),
  kairosState: () => serverGet<KairosState>("/api/kairos/state", 300),
  adminStats: () => serverGet<DashboardStats>("/api/admin/stats", 0),
};

// --- Public reader assistant (browser, no auth) ---
export const assistant = {
  status: async (): Promise<{ enabled: boolean; configured: boolean }> => {
    const res = await fetch(`${PUBLIC_API}/api/assistant/status`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return (await res.json()) as { enabled: boolean; configured: boolean };
  },
  chat: async (messages: AIMessage[]): Promise<AIChatResponse> => {
    const res = await fetch(`${PUBLIC_API}/api/assistant/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages }),
    });
    if (!res.ok) {
      const detail = await res
        .json()
        .catch(() => ({ detail: "تعذّر الاتصال بالمساعد. حاول لاحقاً." }));
      throw new Error(detail.detail || `HTTP ${res.status}`);
    }
    return (await res.json()) as AIChatResponse;
  },
};

// --- Client-side admin helpers (browser, token-based) ---
const TOKEN_KEY = "kassem_admin_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

export async function adminFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const res = await fetch(`${PUBLIC_API}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: "خطأ غير متوقع" }));
    throw new Error(detail.detail || `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const admin = {
  login: (email: string, password: string) =>
    adminFetch<{ access_token: string; role: string; full_name: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  stats: () => adminFetch<DashboardStats>("/api/admin/stats"),
  articles: (params: Record<string, string | number | undefined> = {}) =>
    adminFetch<ArticlePage>(`/api/admin/articles${buildQuery(params)}`),
  article: (id: number) =>
    adminFetch<{
      id: number;
      title_ar: string;
      summary_ar: string;
      body_ar: string;
      image_url: string | null;
      video_url: string | null;
      category_id: number | null;
      region_id: number | null;
      is_breaking: boolean;
      sensitivity: string;
      verification_status: string;
      status: string;
    }>(`/api/admin/articles/${id}`),
  categories: () => adminFetch<Category[]>("/api/admin/categories"),
  regions: () => adminFetch<Region[]>("/api/regions"),
  publish: (id: number, note = "") =>
    adminFetch<Article>(`/api/admin/articles/${id}/publish`, { method: "POST", body: JSON.stringify({ note }) }),
  approve: (id: number, note = "") =>
    adminFetch<Article>(`/api/admin/articles/${id}/approve`, { method: "POST", body: JSON.stringify({ note }) }),
  reject: (id: number, note = "") =>
    adminFetch<Article>(`/api/admin/articles/${id}/reject`, { method: "POST", body: JSON.stringify({ note }) }),
  unpublish: (id: number, note = "") =>
    adminFetch<Article>(`/api/admin/articles/${id}/unpublish`, { method: "POST", body: JSON.stringify({ note }) }),
  updateArticle: (id: number, patch: Partial<Article>) =>
    adminFetch<Article>(`/api/admin/articles/${id}`, { method: "PATCH", body: JSON.stringify(patch) }),
  deleteArticle: (id: number) =>
    adminFetch<void>(`/api/admin/articles/${id}`, { method: "DELETE" }),
  // Multipart upload: the browser must set the boundary, so Content-Type is
  // deliberately NOT set here (adminFetch would force application/json).
  uploadArticleVideo: async (file: File) => {
    const token = getToken();
    const body = new FormData();
    body.append("file", file);
    const res = await fetch(`${PUBLIC_API}/api/admin/uploads/videos`, {
      method: "POST",
      body,
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({ detail: "خطأ غير متوقع" }));
      throw new Error(detail.detail || `HTTP ${res.status}`);
    }
    return (await res.json()) as { url: string; filename: string; size_bytes: number };
  },
  deleteArticleVideo: (filename: string) =>
    adminFetch<void>(`/api/admin/uploads/videos/${encodeURIComponent(filename)}`, {
      method: "DELETE",
    }),
  duplicates: (limit = 300) =>
    adminFetch<DuplicateItem[]>(`/api/admin/duplicates?limit=${limit}`),
  deleteDuplicate: (id: number) =>
    adminFetch<void>(`/api/admin/duplicates/${id}`, { method: "DELETE" }),
  clearDuplicates: () =>
    adminFetch<void>(`/api/admin/duplicates`, { method: "DELETE" }),
  sources: () => adminFetch<Source[]>("/api/admin/sources"),
  updateSource: (id: number, patch: Partial<Source>) =>
    adminFetch<Source>(`/api/admin/sources/${id}`, { method: "PATCH", body: JSON.stringify(patch) }),
  createSource: (payload: Partial<Source>) =>
    adminFetch<Source>("/api/admin/sources", { method: "POST", body: JSON.stringify(payload) }),
  testSource: (id: number) =>
    adminFetch<{ ok: boolean; message: string; entries: number }>(`/api/admin/sources/${id}/test`, { method: "POST" }),
  rules: () => adminFetch<Rule[]>("/api/admin/rules"),
  updateRule: (key: string, value: string) =>
    adminFetch<Rule>(`/api/admin/rules/${key}`, { method: "PUT", body: JSON.stringify({ value }) }),
  runs: () => adminFetch<IngestionRun[]>("/api/admin/runs"),
  errors: () => adminFetch<IngestionError[]>("/api/admin/errors"),
  runIngestion: () => adminFetch<IngestionRun>("/api/admin/ingestion/run", { method: "POST" }),
  pause: () => adminFetch<{ paused: boolean }>("/api/admin/ingestion/pause", { method: "POST" }),
  resume: () => adminFetch<{ paused: boolean }>("/api/admin/ingestion/resume", { method: "POST" }),
  ingestionState: () => adminFetch<{ paused: boolean; auto_publish_enabled: boolean }>("/api/admin/ingestion/state"),
  generateKairos: () => adminFetch<Article>("/api/admin/kairos/generate", { method: "POST" }),
  classificationFlags: (hours = 72) =>
    adminFetch<ClassificationFlags>(`/api/admin/classification/flags?hours=${hours}`),
  reclassify: (
    id: number,
    patch: { category_slug?: string; region_slug?: string; country_iso?: string },
  ) => {
    const params = new URLSearchParams();
    if (patch.category_slug) params.set("category_slug", patch.category_slug);
    if (patch.region_slug) params.set("region_slug", patch.region_slug);
    if (patch.country_iso) params.set("country_iso", patch.country_iso);
    const qs = params.toString();
    return adminFetch<Article>(`/api/admin/articles/${id}/reclassify${qs ? `?${qs}` : ""}`, {
      method: "PATCH",
      body: JSON.stringify({}),
    });
  },
  aiStatus: () => adminFetch<AIStatus>("/api/admin/ai/status"),
  aiChat: (messages: AIMessage[], context = "") =>
    adminFetch<AIChatResponse>("/api/admin/ai/chat", {
      method: "POST",
      body: JSON.stringify({ messages, context }),
    }),
  aiEnrich: (id: number, apply = false) =>
    adminFetch<AIEnrichResponse>(`/api/admin/ai/articles/${id}/enrich?apply=${apply}`, {
      method: "POST",
    }),
};
