"use client";

import { useEffect, useState } from "react";
import AdminPageHeader from "@/components/AdminPageHeader";
import { admin } from "@/lib/api";
import type { ClassificationFlag, ClassificationFlags, DashboardStats } from "@/lib/types";
import { timeAgo } from "@/lib/format";

function StatCard({ label, value, accent = false }: { label: string; value: number | string; accent?: boolean }) {
  return (
    <div className={`stat-tile border-t-2 ${accent ? "border-t-brand" : "border-t-edge"}`}>
      <div className="text-[11px] font-bold text-ink-muted">{label}</div>
      <div className={`mt-2 font-display text-3xl font-extrabold ${accent ? "text-brand-bright" : "text-ink"}`}>
        {value}
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [state, setState] = useState<{ paused: boolean; auto_publish_enabled: boolean } | null>(null);
  const [kairosMsg, setKairosMsg] = useState("");
  const [flags, setFlags] = useState<ClassificationFlags | null>(null);
  const [flagsMsg, setFlagsMsg] = useState("");
  const [fixingId, setFixingId] = useState<number | null>(null);

  async function load() {
    try {
      const [s, ingState] = await Promise.all([admin.stats(), admin.ingestionState()]);
      setStats(s);
      setState(ingState);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر تحميل البيانات");
    }
    try {
      setFlags(await admin.classificationFlags(72));
    } catch {
      setFlags({ count: 0, items: [] });
    }
  }

  async function applyFix(flag: ClassificationFlag) {
    if (!flag.suggested_region && !flag.suggested_category) return;
    setFixingId(flag.id);
    setFlagsMsg("");
    try {
      await admin.reclassify(flag.id, {
        region_slug: flag.suggested_region ?? undefined,
        category_slug: flag.suggested_category ?? undefined,
      });
      setFlagsMsg(`تم تصحيح تصنيف الخبر #${flag.id}`);
      setFlags(await admin.classificationFlags(72));
    } catch (err) {
      setFlagsMsg(err instanceof Error ? err.message : "تعذر التصحيح");
    } finally {
      setFixingId(null);
    }
  }

  async function generateKairos() {
    setKairosMsg("");
    try {
      const a = await admin.generateKairos();
      setKairosMsg(`تم توليد/استرجاع تحليل كاييروس: «${a.title_ar}»`);
    } catch (err) {
      setKairosMsg(err instanceof Error ? err.message : "تعذر توليد التحليل");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function runIngestion() {
    setBusy(true);
    try {
      await admin.runIngestion();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر تشغيل التوريد");
    } finally {
      setBusy(false);
    }
  }

  async function togglePause() {
    if (!state) return;
    setBusy(true);
    try {
      if (state.paused) await admin.resume();
      else await admin.pause();
      await load();
    } finally {
      setBusy(false);
    }
  }

  if (error) return <p className="text-brand-bright">{error}</p>;
  if (!stats) return <p className="text-ink-muted">جارٍ تحميل لوحة المعلومات…</p>;

  return (
    <div className="space-y-6">
      <AdminPageHeader
        title="نظرة عامة"
        description="حالة التوريد والنشر، وأحدث المهام والتنبيهات التحريرية."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <button onClick={runIngestion} disabled={busy} className="btn-primary text-sm">
              {busy ? "جارٍ التنفيذ…" : "تشغيل التوريد الآن"}
            </button>
            <button onClick={generateKairos} className="btn-ghost text-sm">
              توليد تحليل كاييروس
            </button>
            <button onClick={togglePause} disabled={busy} className="btn-ghost text-sm">
              {state?.paused ? "استئناف التوريد" : "إيقاف التوريد مؤقتاً"}
            </button>
          </div>
        }
      />
      {kairosMsg && <p className="text-sm text-ink">{kairosMsg}</p>}

      {state?.paused && (
        <div className="badge border-amber-800 bg-amber-900/30 px-3 py-2 text-amber-300">
          خط التوريد موقوف مؤقتاً
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="إجمالي الأخبار المجمّعة" value={stats.total_articles} />
        <StatCard label="منشورة" value={stats.published} accent />
        <StatCard label="بانتظار المراجعة" value={stats.pending_review} accent />
        <StatCard label="مكرّرة (مُكتشفة)" value={stats.duplicates_detected} />
        <StatCard label="عمليات جلب فاشلة" value={stats.failed_fetches} />
        <StatCard label="مصادر نشطة" value={`${stats.active_sources}/${stats.total_sources}`} />
        <StatCard label="أحداث مجمّعة" value={stats.total_events} />
        <StatCard label="آخر تشغيل" value={stats.last_run ? stats.last_run.status : "—"} />
      </div>

      <section className="card p-5">
        <div className="section-title mb-3">
          <h2 className="text-lg">آخر عمليات التوريد</h2>
        </div>
        {stats.recent_runs.length ? (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead className="text-ink-muted text-xs">
                <tr className="text-right">
                  <th className="py-2 px-2">#</th>
                  <th className="py-2 px-2">الحالة</th>
                  <th className="py-2 px-2">مصادر</th>
                  <th className="py-2 px-2">جديد</th>
                  <th className="py-2 px-2">منشور</th>
                  <th className="py-2 px-2">مراجعة</th>
                  <th className="py-2 px-2">مكرر</th>
                  <th className="py-2 px-2">الوقت</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_runs.map((r) => (
                  <tr key={r.id} className="border-t border-edge">
                    <td className="py-2 px-2">{r.id}</td>
                    <td className="py-2 px-2">{r.status}</td>
                    <td className="py-2 px-2">{r.sources_ok}/{r.sources_total}</td>
                    <td className="py-2 px-2">{r.articles_new}</td>
                    <td className="py-2 px-2">{r.articles_published}</td>
                    <td className="py-2 px-2">{r.articles_review}</td>
                    <td className="py-2 px-2">{r.duplicates}</td>
                    <td className="py-2 px-2">{timeAgo(r.started_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-ink-muted">لا توجد عمليات توريد بعد.</p>
        )}
      </section>

      <section className="card p-5">
        <div className="section-title mb-3">
          <h2 className="text-lg">أحدث الأخطاء</h2>
        </div>
        {stats.recent_errors.length ? (
          <ul className="space-y-2 text-sm">
            {stats.recent_errors.map((e) => (
              <li key={e.id} className="border-b border-edge pb-2 last:border-0">
                <span className="text-ink-muted text-xs">[{timeAgo(e.created_at)}]</span>{" "}
                <span className="text-brand-bright">مصدر #{e.source_id ?? "—"}:</span> {e.message}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-ink-muted">لا توجد أخطاء مسجّلة.</p>
        )}
      </section>

      <section className="card p-5">
        <div className="section-title mb-3">
          <h2 className="text-lg">مراقبة التصنيف (آخر 72 ساعة)</h2>
        </div>
        {flagsMsg && <p className="text-sm text-ink mb-2">{flagsMsg}</p>}
        {flags && flags.count > 0 ? (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead className="text-ink-muted text-xs">
                <tr className="text-right">
                  <th className="py-2 px-2">الخبر</th>
                  <th className="py-2 px-2">التصنيف الحالي</th>
                  <th className="py-2 px-2">المنطقة</th>
                  <th className="py-2 px-2">المشكلة</th>
                  <th className="py-2 px-2">الاقتراح</th>
                  <th className="py-2 px-2"></th>
                </tr>
              </thead>
              <tbody>
                {flags.items.map((f) => (
                  <tr key={f.id} className="border-t border-edge align-top">
                    <td className="py-2 px-2 max-w-[240px]">
                      #{f.id} <span className="text-ink-muted">{f.title}</span>
                    </td>
                    <td className="py-2 px-2">
                      {f.category || "—"} / {f.region || "—"}
                      {f.detected_country ? ` / ${f.detected_country}` : ""}
                    </td>
                    <td className="py-2 px-2">{f.region || "بدون"}</td>
                    <td className="py-2 px-2 text-brand-bright text-xs">{f.issues.join("، ")}</td>
                    <td className="py-2 px-2 text-xs">
                      {f.suggested_region || f.suggested_category
                        ? `${f.suggested_region || "—"} / ${f.suggested_category || "—"}`
                        : "—"}
                    </td>
                    <td className="py-2 px-2">
                      {f.suggested_region || f.suggested_category ? (
                        <button
                          onClick={() => applyFix(f)}
                          disabled={fixingId === f.id}
                          className="btn-ghost text-xs"
                        >
                          {fixingId === f.id ? "جارٍ…" : "تصحيح"}
                        </button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-ink-muted">
            {flags === null ? "جارٍ الفحص…" : "لا توجد تصنيفات مشبوهة في هذه الفترة."}
          </p>
        )}
      </section>
    </div>
  );
}
