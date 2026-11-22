"use client";

import { useEffect, useState } from "react";
import AdminPageHeader from "@/components/AdminPageHeader";
import { admin } from "@/lib/api";
import type { Source } from "@/lib/types";
import { timeAgo } from "@/lib/format";

export default function AdminSourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState<number | null>(null);

  async function load() {
    setLoading(true);
    try {
      setSources(await admin.sources());
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر تحميل المصادر");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function toggle(source: Source, field: "is_active" | "requires_review") {
    setBusy(source.id);
    setMsg("");
    try {
      const updated = await admin.updateSource(source.id, { [field]: !source[field] } as Partial<Source>);
      setSources((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر التحديث");
    } finally {
      setBusy(null);
    }
  }

  async function test(source: Source) {
    setBusy(source.id);
    setMsg("");
    try {
      const result = await admin.testSource(source.id);
      setMsg(`[${source.name_ar}] ${result.ok ? "✓" : "✗"} ${result.message}`);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "تعذر اختبار المصدر");
    } finally {
      setBusy(null);
    }
  }

  const [form, setForm] = useState({
    name_ar: "",
    name_en: "",
    slug: "",
    feed_url: "",
    homepage: "",
    trust_tier: 2,
    requires_review: true,
    is_active: true,
  });
  const [saving, setSaving] = useState(false);

  function setField(field: keyof typeof form, value: string | number | boolean) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function addSource() {
    setSaving(true);
    setError("");
    setMsg("");
    try {
      const created = await admin.createSource({
        ...form,
        slug: form.slug.trim() || form.name_en.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-"),
        language: "ar",
      });
      setMsg(`تمت إضافة المصدر «${created.name_ar}». سيُلتقط في دورة التوريد القادمة.`);
      setForm({ name_ar: "", name_en: "", slug: "", feed_url: "", homepage: "", trust_tier: 2, requires_review: true, is_active: true });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر إضافة المصدر");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="text-ink-muted">جارٍ التحميل…</p>;

  return (
    <div>
      <AdminPageHeader
        title="إدارة المصادر"
        description="إضافة مصادر جديدة (RSS/Atom)، تفعيل/تعطيل المصادر وتحديد خضوعها للمراجعة الإلزامية، مع اختبار مباشر لخلاصة RSS."
      />
      {error && <p className="mb-3 text-brand-bright text-sm">{error}</p>}
      {msg && <p className="mb-3 text-sm text-ink">{msg}</p>}

      <section className="card p-4 space-y-3">
        <h2 className="font-extrabold">إضافة مصدر جديد</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="col-span-2 grid gap-1 text-xs font-semibold text-ink-muted">
            رابط الخلاصة (RSS/Atom) *
            <input
              dir="ltr"
              placeholder="https://example.com/rss.xml"
              value={form.feed_url}
              onChange={(e) => setField("feed_url", e.target.value)}
              className="input"
            />
          </label>
          <label className="grid gap-1 text-xs font-semibold text-ink-muted">
            الاسم بالعربية *
            <input value={form.name_ar} onChange={(e) => setField("name_ar", e.target.value)} className="input" />
          </label>
          <label className="grid gap-1 text-xs font-semibold text-ink-muted">
            الاسم بالإنجليزية *
            <input
              dir="ltr"
              value={form.name_en}
              onChange={(e) => setField("name_en", e.target.value)}
              className="input"
            />
          </label>
          <label className="grid gap-1 text-xs font-semibold text-ink-muted">
            المعرّف (slug) — يُترك فارغاً ليُولّد تلقائياً
            <input dir="ltr" value={form.slug} onChange={(e) => setField("slug", e.target.value)} className="input" />
          </label>
          <label className="grid gap-1 text-xs font-semibold text-ink-muted">
            الصفحة الرئيسية للمصدر
            <input dir="ltr" value={form.homepage} onChange={(e) => setField("homepage", e.target.value)} className="input" />
          </label>
          <label className="grid gap-1 text-xs font-semibold text-ink-muted">
            درجة الثقة (1 أعلى)
            <select value={form.trust_tier} onChange={(e) => setField("trust_tier", Number(e.target.value))} className="input">
              <option value={1}>1 — وكالات موثوقة (نشر تلقائي)</option>
              <option value={2}>2 — وسائط مهنية (نشر حسب القواعد)</option>
              <option value={3}>3 — مجمّعات وأخرى (يُنصح بالمراجعة)</option>
            </select>
          </label>
          <div className="flex items-end gap-4 pt-1">
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.requires_review} onChange={(e) => setField("requires_review", e.target.checked)} />
              مراجعة إلزامية
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={form.is_active} onChange={(e) => setField("is_active", e.target.checked)} />
              مفعّل
            </label>
          </div>
        </div>
        <button
          onClick={addSource}
          disabled={saving || !form.feed_url.trim() || !form.name_ar.trim() || !form.name_en.trim()}
          className="btn-primary px-4 py-2"
        >
          {saving ? "جارٍ الحفظ…" : "إضافة المصدر"}
        </button>
      </section>

      <div className="space-y-3">
        {sources.map((s) => (
          <article key={s.id} className="card p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-bold">{s.name_ar}</h3>
                  <span className="badge border-edge text-ink-muted">ثقة {s.trust_tier}</span>
                  <span className={`badge ${s.is_active ? "border-green-800 text-green-300 bg-green-900/30" : "border-edge text-ink-muted"}`}>
                    {s.is_active ? "نشط" : "معطّل"}
                  </span>
                  {s.requires_review && (
                    <span className="badge border-amber-800 bg-amber-900/30 text-amber-300">يراجع إلزامياً</span>
                  )}
                </div>
                <p className="mt-1 text-xs text-ink-muted break-all" dir="ltr">
                  {s.feed_url || "—"}
                </p>
                {s.rights_note && <p className="mt-1 text-xs text-ink-muted">{s.rights_note}</p>}
                <p className="mt-1 text-xs text-ink-muted">
                  آخر جلب: {s.last_fetched_at ? timeAgo(s.last_fetched_at) : "لم يتم"} — الحالة: {s.last_status}
                </p>
              </div>
              <div className="flex flex-col gap-2 shrink-0">
                <button onClick={() => test(s)} disabled={busy === s.id || !s.feed_url} className="btn-ghost px-3 py-1.5 text-xs">
                  اختبار الخلاصة
                </button>
                <button onClick={() => toggle(s, "is_active")} disabled={busy === s.id} className="btn-ghost px-3 py-1.5 text-xs">
                  {s.is_active ? "تعطيل" : "تفعيل"}
                </button>
                <button onClick={() => toggle(s, "requires_review")} disabled={busy === s.id} className="btn-ghost px-3 py-1.5 text-xs">
                  {s.requires_review ? "إلغاء المراجعة الإلزامية" : "فرض المراجعة"}
                </button>
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
