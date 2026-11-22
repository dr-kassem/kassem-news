"use client";

import { useEffect, useState } from "react";
import AdminPageHeader from "@/components/AdminPageHeader";
import { admin } from "@/lib/api";
import type { DuplicateItem } from "@/lib/types";
import { timeAgo } from "@/lib/format";

export default function DuplicatesPage() {
  const [items, setItems] = useState<DuplicateItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<number | "all" | null>(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      setItems(await admin.duplicates(300));
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر تحميل الأخبار المكرّرة");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function remove(id: number) {
    if (!confirm("هل أنت متأكد من حذف هذا السجل المكرّر؟")) return;
    setBusyId(id);
    setError("");
    try {
      await admin.deleteDuplicate(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر الحذف");
    } finally {
      setBusyId(null);
    }
  }

  async function clearAll() {
    if (!confirm("هل أنت متأكد من حذف كل سجلات الأخبار المكرّرة؟")) return;
    setBusyId("all");
    setError("");
    try {
      await admin.clearDuplicates();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر الحذف");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <AdminPageHeader
        title="الأخبار المكرّرة"
        description="هذه الأخبار رُصدت كمكرّرة أثناء جلب المصادر ولم تُنشر. الحذف يزيل السجل فقط."
        actions={
          <div className="flex items-center gap-2">
            <span className="text-sm text-ink-muted">{items.length} سجل</span>
            <button onClick={load} className="btn-ghost text-sm">
              تحديث
            </button>
            {items.length > 0 && (
              <button
                onClick={clearAll}
                disabled={busyId === "all"}
                className="btn-ghost text-sm text-brand-bright border-brand/60 hover:bg-brand/10"
              >
                {busyId === "all" ? "جارٍ الحذف…" : "حذف الكل"}
              </button>
            )}
          </div>
        }
      />

      {error && <p className="mb-3 text-brand-bright text-sm">{error}</p>}
      {loading ? (
        <p className="text-ink-muted">جارٍ التحميل…</p>
      ) : items.length === 0 ? (
        <div className="card p-8 text-center text-ink-muted">لا توجد أخبار مكرّرة مسجّلة.</div>
      ) : (
        <div className="overflow-x-auto card p-4">
          <table className="data-table">
            <thead className="text-ink-muted text-xs">
              <tr className="text-right">
                <th className="py-2 px-2">#</th>
                <th className="py-2 px-2">الخبر المكرّر (الرابط)</th>
                <th className="py-2 px-2">نسبة التشابه</th>
                <th className="py-2 px-2">الخبر الأصلي</th>
                <th className="py-2 px-2">الوقت</th>
                <th className="py-2 px-2"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((d) => (
                <tr key={d.id} className="border-t border-edge align-top">
                  <td className="py-2 px-2">{d.id}</td>
                  <td className="py-2 px-2 max-w-[260px]">
                    {d.url ? (
                      <a
                        href={d.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="link-muted break-all"
                      >
                        {d.url}
                      </a>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="py-2 px-2">{Math.round((d.similarity || 0) * 100)}%</td>
                  <td className="py-2 px-2 max-w-[240px]">
                    {d.duplicate_of_id ? (
                      <a
                        href={`/article/${d.duplicate_of_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="link-muted"
                      >
                        {d.duplicate_of_title || `#${d.duplicate_of_id}`}
                      </a>
                    ) : (
                      <span className="text-ink-muted">— (حُذف الأصل)</span>
                    )}
                  </td>
                  <td className="py-2 px-2 text-xs text-ink-muted">{timeAgo(d.created_at)}</td>
                  <td className="py-2 px-2">
                    <button
                      onClick={() => remove(d.id)}
                      disabled={busyId === d.id}
                      className="btn-ghost text-xs text-brand-bright border-brand/60 hover:bg-brand/10"
                    >
                      {busyId === d.id ? "جارٍ…" : "حذف"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
