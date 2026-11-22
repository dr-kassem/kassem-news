import type { MetadataRoute } from "next";
import { api } from "@/lib/api";

export const revalidate = 3600;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const base = process.env.SITE_URL || "https://kassem.news";
  const meta = await api.meta();
  const recent = await api.articles({ page_size: 100 });

  const staticRoutes: MetadataRoute.Sitemap = [
    "",
    "/breaking",
    "/search",
  ].map((path) => ({ url: `${base}${path}`, changeFrequency: "hourly" as const, priority: 1 }));

  const categoryRoutes: MetadataRoute.Sitemap = (meta?.categories ?? []).map((c) => ({
    url: `${base}/section/${c.slug}`,
    changeFrequency: "hourly",
    priority: 0.8,
  }));

  const regionRoutes: MetadataRoute.Sitemap = (meta?.regions ?? []).map((r) => ({
    url: `${base}/region/${r.slug}`,
    changeFrequency: "hourly",
    priority: 0.8,
  }));

  const articleRoutes: MetadataRoute.Sitemap = (recent?.items ?? []).map((a) => ({
    url: `${base}/article/${a.id}`,
    lastModified: new Date(a.updated_at),
    changeFrequency: "daily",
    priority: 0.7,
  }));

  return [...staticRoutes, ...categoryRoutes, ...regionRoutes, ...articleRoutes];
}
