export type Category = {
  id: number;
  slug: string;
  name_ar: string;
  name_en: string;
  nav_order: number;
  show_in_nav: boolean;
};

export type Region = { id: number; slug: string; name_ar: string; name_en: string };

export type Source = {
  id: number;
  slug: string;
  name_ar: string;
  name_en: string;
  type: string;
  feed_url: string;
  homepage: string;
  language: string;
  country_iso: string | null;
  trust_tier: number;
  requires_review: boolean;
  is_active: boolean;
  fetch_interval_minutes: number;
  rights_note: string;
  last_fetched_at: string | null;
  last_status: string;
};

export type Article = {
  id: number;
  title_ar: string;
  summary_ar: string;
  url: string;
  image_url: string | null;
  video_url: string | null;
  author: string;
  is_breaking: boolean;
  sensitivity: "normal" | "sensitive";
  verification_status: "confirmed" | "attributed" | "developing" | "unconfirmed";
  status: string;
  source_published_at: string | null;
  published_at: string | null;
  updated_at: string;
  category: Category | null;
  region: Region | null;
  source: Source | null;
};

export type ArticleDetail = Article & {
  body_ar: string;
  tags: { id: number; slug: string; name_ar: string }[];
  related: Article[];
  event_id: number | null;
  is_generated_summary: boolean;
};

export type EventItem = {
  id: number;
  title_ar: string;
  summary_ar: string;
  is_developing: boolean;
  article_count: number;
  first_seen_at: string;
  last_update_at: string;
};

export type ArticlePage = {
  items: Article[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
};

export type StrikeReport = {
  id: string;
  short_code: string;
  type: string;
  type_label: string;
  category: string;
  city_name: string;
  description: string;
  lat: number | null;
  lon: number | null;
  created_at: string;
  approximate_location: boolean;
  location_precision_m: number | null;
  evidence_label: string;
};

export type StrikeTypeCount = {
  type: string;
  label: string;
  count: number;
};

export type StrikeFeed = {
  items: StrikeReport[];
  types: StrikeTypeCount[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  updated_at: string | null;
};

export type Meta = {
  app_name: string;
  slogan_ar: string;
  slogan_en: string;
  categories: Category[];
  regions: Region[];
};

export type KairosState = {
  enabled: boolean;
  author: string;
  stance: string;
  interval_hours: number;
};

export type ClassificationFlag = {
  id: number;
  title: string;
  category: string;
  region: string;
  country: string;
  detected_country: string;
  suggested_category: string | null;
  suggested_region: string | null;
  issues: string[];
};

export type ClassificationFlags = {
  count: number;
  items: ClassificationFlag[];
};

export type DashboardStats = {
  total_articles: number;
  published: number;
  pending_review: number;
  duplicates_detected: number;
  failed_fetches: number;
  active_sources: number;
  total_sources: number;
  total_events: number;
  last_run: IngestionRun | null;
  recent_runs: IngestionRun[];
  recent_errors: IngestionError[];
};

export type IngestionRun = {
  id: number;
  trigger: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  sources_total: number;
  sources_ok: number;
  sources_failed: number;
  articles_fetched: number;
  articles_new: number;
  articles_published: number;
  articles_review: number;
  duplicates: number;
  errors: number;
  notes: string;
};

export type IngestionError = {
  id: number;
  run_id: number | null;
  source_id: number | null;
  message: string;
  retry_count: number;
  created_at: string;
};

export type Rule = {
  id: number;
  key: string;
  value: string;
  value_type: string;
  label_ar: string;
  is_active: boolean;
  updated_at: string;
};

export type DuplicateItem = {
  id: number;
  url: string;
  similarity: number;
  created_at: string;
  duplicate_of_id: number | null;
  duplicate_of_title: string;
  duplicate_of_url: string;
};

export type AIStatus = {
  enabled: boolean;
  configured: boolean;
  provider: string;
  model: string;
  fallback_models: string[];
  summarize_on_ingest: boolean;
};

export type AIMessage = {
  role: "user" | "assistant";
  content: string;
};

export type AIChatResponse = {
  reply: string;
  model: string;
};

export type AIEnrichResponse = {
  article_id: number;
  title_ar: string;
  summary_ar: string;
  applied: boolean;
  model: string;
};
