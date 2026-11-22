"use client";

import { useEffect, useState } from "react";
import AdminPageHeader from "@/components/AdminPageHeader";
import { admin } from "@/lib/api";
import type { IngestionError, IngestionRun } from "@/lib/types";
import { fullDate, timeAgo } from "@/lib/format";

export default function AdminRunsPage() {
  const [runs, setRuns] = useState<IngestionRun[]>([]);
  const [errors, setErrors] = useState<IngestionError[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"runs" | "errors">("runs");

  async function load() {
    setLoading(true);
    try {
      const [r, e] = await Promise.all([admin.runs(), admin.errors()]);
      setRuns(r);
      setErrors(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (loading) return <p className="text-ink-muted">جارٍ التحميل…</p>;

  return (
    <div>
      <AdminPageHeader
        title="التوريد والسجلات"
        description="سجل دورات جلب الأخبار والأخطاء المسجّلة على مستوى المصادر."
        actions={
          <div className="flex gap-2">
            <button onClick={() => setTab("runs")} className={tab === "runs" ? "btn-primary text-sm" : "btn-ghost text-sm"}>
              عمليات التوريد ({runs.length})
            </button>
            <button onClick={() => setTab("errors")} className={tab === "errors" ? "btn-primary text-sm" : "btn-ghost text-sm"}>
              سجل الأخطاء ({errors.length})
            </button>
          </div>
        }
      />

      {tab === "runs" ? (
        <div className="card overflow-x-auto">
          <table className="data-table">
            <thead className="text-ink-muted text-xs">
              <tr className="text-right">
                <th className="py-2 px-2">#</th>
                <th className="py-2 px-2">البدء</th>
                <th className="py-2 px-2">الحالة</th>
                <th className="py-2 px-2">مصادر</th>
                <th className="py-2 px-2">جلب</th>
                <th className="py-2 px-2">جديد</th>
                <th className="py-2 px-2">منشور</th>
                <th className="py-2 px-2">مراجعة</th>
                <th className="py-2 px-2">مكرر</th>
                <th className="py-2 px-2">أخطاء</th>
                <th className="py-2 px-2">المحفّز</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id} className="border-t border-edge">
                  <td className="py-2 px-2">{r.id}</td>
                  <td className="py-2 px-2 whitespace-nowrap" title={fullDate(r.started_at)}>{timeAgo(r.started_at)}</td>
                  <td className="py-2 px-2">{r.status}</td>
                  <td className="py-2 px-2">{r.sources_ok}/{r.sources_total}</td>
                  <td className="py-2 px-2">{r.articles_fetched}</td>
                  <td className="py-2 px-2">{r.articles_new}</td>
                  <td className="py-2 px-2">{r.articles_published}</td>
                  <td className="py-2 px-2">{r.articles_review}</td>
                  <td className="py-2 px-2">{r.duplicates}</td>
                  <td className="py-2 px-2">{r.errors}</td>
                  <td className="py-2 px-2">{r.trigger}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!runs.length && <p className="text-ink-muted text-sm py-4">لا توجد عمليات توريد.</p>}
        </div>
      ) : (
        <div className="card p-5">
          {errors.length ? (
            <ul className="space-y-2 text-sm">
              {errors.map((e) => (
                <li key={e.id} className="border-b border-edge pb-2 last:border-0">
                  <span className="text-ink-muted text-xs">[{fullDate(e.created_at)}]</span>{" "}
                  <span className="text-brand-bright">مصدر #{e.source_id ?? "—"} (محاولات: {e.retry_count}):</span>{" "}
                  <span dir="ltr" className="break-all">{e.message}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-ink-muted text-sm">لا توجد أخطاء مسجّلة.</p>
          )}
        </div>
      )}
    </div>
  );
}
