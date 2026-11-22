"use client";

import Link from "next/link";
import { useEffect, useState, type ChangeEvent } from "react";
import AdminPageHeader from "@/components/AdminPageHeader";
import { admin } from "@/lib/api";
import type { Article, Category, Region } from "@/lib/types";
import { timeAgo, VERIFICATION_LABELS, VERIFICATION_STYLES } from "@/lib/format";

const STATUS_LABELS: Record<string, string> = {
  published: "منشور",
  review: "مراجعة",
  pending: "بالانتظار",
  rejected: "مرفوض",
  unpublished: "غير منشور",
};

type EditForm = {
  title_ar: string;
  summary_ar: string;
  body_ar: string;
  category_id: string;
  region_id: string;
  video_url: string;
};

const EMPTY_FORM: EditForm = {
  title_ar: "",
  summary_ar: "",
  body_ar: "",
  category_id: "",
  region_id: "",
  video_url: "",
};

export default function ArticlesTable({
  status,
  title,
  emptyMessage,
}: {
  status?: string;
  title: string;
  emptyMessage: string;
}) {
  const [items, setItems] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [q, setQ] = useState("");
  const [categories, setCategories] = useState<Category[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<EditForm>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [uploadingVideo, setUploadingVideo] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await admin.articles({ status, q, page_size: 50 });
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر تحميل الأخبار");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  useEffect(() => {
    Promise.all([
      admin.categories().catch(() => [] as Category[]),
      admin.regions().catch(() => [] as Region[]),
    ]).then(([c, r]) => {
      setCategories(c);
      setRegions(r);
    });
  }, []);

  async function act(id: number, action: "approve" | "reject" | "publish" | "unpublish") {
    setBusyId(id);
    try {
      await admin[action](id, "");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر تنفيذ الإجراء");
    } finally {
      setBusyId(null);
    }
  }

  async function startEdit(id: number) {
    setError("");
    setBusyId(id);
    try {
      const data = await admin.article(id);
      setForm({
        title_ar: data.title_ar,
        summary_ar: data.summary_ar,
        body_ar: data.body_ar,
        category_id: data.category_id ? String(data.category_id) : "",
        region_id: data.region_id ? String(data.region_id) : "",
        video_url: data.video_url || "",
      });
      setEditingId(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر تحميل الخبر");
    } finally {
      setBusyId(null);
    }
  }

  async function onVideoFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setUploadingVideo(true);
    setError("");
    try {
      const { filename, url } = await admin.uploadArticleVideo(file);
      const previous = form.video_url;
      setForm((f) => ({ ...f, video_url: url }));
      if (previous && previous.includes("/uploads/")) {
        const prevName = previous.split("/").pop();
        if (prevName && prevName !== filename) admin.deleteArticleVideo(prevName).catch(() => {});
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر رفع الفيديو");
    } finally {
      setUploadingVideo(false);
    }
  }

  function removeVideo() {
    const current = form.video_url;
    setForm((f) => ({ ...f, video_url: "" }));
    if (current && current.includes("/uploads/")) {
      const name = current.split("/").pop();
      if (name) admin.deleteArticleVideo(name).catch(() => {});
    }
  }

  async function saveEdit() {
    if (editingId === null) return;
    setSaving(true);
    setError("");
    try {
      await admin.updateArticle(editingId, {
        title_ar: form.title_ar,
        summary_ar: form.summary_ar,
        body_ar: form.body_ar,
        category_id: form.category_id ? Number(form.category_id) : null,
        region_id: form.region_id ? Number(form.region_id) : null,
        video_url: form.video_url || null,
      } as Partial<Article>);
      setEditingId(null);
      setForm(EMPTY_FORM);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر حفظ التعديلات");
    } finally {
      setSaving(false);
    }
  }

  async function remove(id: number) {
    if (!confirm("هل أنت متأكد من حذف هذا الخبر نهائياً؟")) return;
    setBusyId(id);
    setError("");
    try {
      await admin.deleteArticle(id);
      if (editingId === id) {
        setEditingId(null);
        setForm(EMPTY_FORM);
      }
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر حذف الخبر");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <AdminPageHeader
        title={title}
        description="مراجعة الأخبار، تعديل المحتوى، والتحكم في حالة النشر."
        actions={
          <form
            onSubmit={(e) => {
              e.preventDefault();
              load();
            }}
            className="flex gap-2"
          >
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="بحث في العناوين…"
              className="input w-56"
            />
            <button type="submit" className="btn-ghost text-sm">
              بحث
            </button>
          </form>
        }
      />

      {error && <p className="mb-3 text-brand-bright text-sm">{error}</p>}
      {loading ? (
        <p className="text-ink-muted">جارٍ التحميل…</p>
      ) : items.length === 0 ? (
        <div className="border-y border-edge bg-surface/50 p-10 text-center text-ink-muted">{emptyMessage}</div>
      ) : (
        <div className="space-y-3">
          {items.map((a) => (
            <article key={a.id} className="card card-hover border-r-4 border-r-brand/60 p-4">
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className="font-mono text-[11px] text-ink-muted">#{a.id}</span>
                <span className={`badge ${a.status === "published" ? "border-green-800 text-green-300 bg-green-900/30" : "border-edge text-ink-muted"}`}>
                  {STATUS_LABELS[a.status] ?? a.status}
                </span>
                {a.category && <span className="badge border-brand/60 text-brand-bright bg-brand/10">{a.category.name_ar}</span>}
                {a.sensitivity === "sensitive" && (
                  <span className="badge border-amber-800 bg-amber-900/30 text-amber-300">حساس</span>
                )}
                <span className={`badge ${VERIFICATION_STYLES[a.verification_status]}`}>
                  {VERIFICATION_LABELS[a.verification_status]}
                </span>
              </div>

              {editingId === a.id ? (
                <div className="space-y-3 mt-2">
                  <div>
                    <label className="block text-xs text-ink-muted mb-1">العنوان</label>
                    <input
                      value={form.title_ar}
                      onChange={(e) => setForm({ ...form, title_ar: e.target.value })}
                      className="input w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-ink-muted mb-1">الملخص</label>
                    <textarea
                      value={form.summary_ar}
                      onChange={(e) => setForm({ ...form, summary_ar: e.target.value })}
                      rows={2}
                      className="input w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-ink-muted mb-1">المتن</label>
                    <textarea
                      value={form.body_ar}
                      onChange={(e) => setForm({ ...form, body_ar: e.target.value })}
                      rows={6}
                      className="input w-full"
                    />
                  </div>
                  <div className="flex flex-wrap gap-3">
                    <div>
                      <label className="block text-xs text-ink-muted mb-1">القسم</label>
                      <select
                        value={form.category_id}
                        onChange={(e) => setForm({ ...form, category_id: e.target.value })}
                        className="input"
                      >
                        <option value="">— بدون —</option>
                        {categories.map((c) => (
                          <option key={c.id} value={c.id}>{c.name_ar}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs text-ink-muted mb-1">المنطقة</label>
                      <select
                        value={form.region_id}
                        onChange={(e) => setForm({ ...form, region_id: e.target.value })}
                        className="input"
                      >
                        <option value="">— بدون —</option>
                        {regions.map((r) => (
                          <option key={r.id} value={r.id}>{r.name_ar}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs text-ink-muted mb-1">فيديو الخبر</label>
                    {form.video_url ? (
                      <div className="flex flex-wrap items-center gap-3">
                        <video
                          src={form.video_url}
                          controls
                          preload="metadata"
                          className="h-28 w-auto rounded border border-edge bg-black"
                        />
                        <div className="space-y-2">
                          <label className="btn-ghost px-3 py-1.5 text-xs inline-block cursor-pointer">
                            {uploadingVideo ? "جارٍ الرفع…" : "استبدال الفيديو"}
                            <input
                              type="file"
                              accept="video/mp4,video/webm,video/quicktime,video/ogg"
                              onChange={onVideoFile}
                              disabled={uploadingVideo}
                              className="hidden"
                            />
                          </label>
                          <button onClick={removeVideo} className="btn-ghost px-3 py-1.5 text-xs block text-brand-bright border-brand/60 hover:bg-brand/10">
                            إزالة الفيديو
                          </button>
                        </div>
                      </div>
                    ) : (
                      <label className="btn-ghost px-3 py-1.5 text-xs inline-block cursor-pointer">
                        {uploadingVideo ? "جارٍ الرفع…" : "رفع فيديو"}
                        <input
                          type="file"
                          accept="video/mp4,video/webm,video/quicktime,video/ogg"
                          onChange={onVideoFile}
                          disabled={uploadingVideo}
                          className="hidden"
                        />
                      </label>
                    )}
                    <p className="mt-1 text-[11px] text-ink-muted">
                      الصيغ المدعومة: mp4، webm، mov. يُحفظ الفيديو عند حفظ التعديلات.
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button onClick={saveEdit} disabled={saving} className="btn-primary px-3 py-1.5 text-xs">
                      {saving ? "جارٍ الحفظ…" : "حفظ"}
                    </button>
                    <button
                      onClick={() => { setEditingId(null); setForm(EMPTY_FORM); }}
                      className="btn-ghost px-3 py-1.5 text-xs"
                    >
                      إلغاء
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <h3 className="font-display text-lg font-extrabold leading-snug">
                    <Link href={`/article/${a.id}`} target="_blank" className="hover:text-brand-bright">
                      {a.title_ar}
                    </Link>
                  </h3>
                  <div className="mt-1 text-xs text-ink-muted flex flex-wrap gap-x-2 gap-y-1">
                    <span>{a.source?.name_ar || "تحرير يدوي"}</span>
                    <span aria-hidden>•</span>
                    <span>{timeAgo(a.published_at || a.source_published_at)}</span>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2 border-t border-edge pt-3">
                    {a.status !== "published" && (
                      <>
                        <button onClick={() => act(a.id, "approve")} disabled={busyId === a.id} className="btn-primary px-3 py-1.5 text-xs">
                          اعتماد ونشر
                        </button>
                        <button onClick={() => act(a.id, "reject")} disabled={busyId === a.id} className="btn-ghost px-3 py-1.5 text-xs">
                          رفض
                        </button>
                      </>
                    )}
                    {a.status === "published" && (
                      <button onClick={() => act(a.id, "unpublish")} disabled={busyId === a.id} className="btn-ghost px-3 py-1.5 text-xs">
                        إلغاء النشر
                      </button>
                    )}
                    <button onClick={() => startEdit(a.id)} disabled={busyId === a.id} className="btn-ghost px-3 py-1.5 text-xs">
                      تعديل
                    </button>
                    <button onClick={() => remove(a.id)} disabled={busyId === a.id} className="btn-ghost px-3 py-1.5 text-xs text-brand-bright border-brand/60 hover:bg-brand/10">
                      حذف
                    </button>
                  </div>
                </>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
