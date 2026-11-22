"use client";

import { useEffect, useState } from "react";
import AdminPageHeader from "@/components/AdminPageHeader";
import { admin } from "@/lib/api";
import type { Rule } from "@/lib/types";

export default function AdminRulesPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    try {
      const data = await admin.rules();
      setRules(data);
      setDrafts(Object.fromEntries(data.map((r) => [r.key, r.value])));
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر تحميل القواعد");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function save(key: string) {
    setMsg("");
    setError("");
    try {
      const updated = await admin.updateRule(key, drafts[key]);
      setRules((prev) => prev.map((r) => (r.key === key ? updated : r)));
      setMsg(`تم حفظ القاعدة: ${updated.label_ar || key}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر الحفظ");
    }
  }

  if (loading) return <p className="text-ink-muted">جارٍ التحميل…</p>;

  return (
    <div>
      <AdminPageHeader
        title="قواعد النشر"
        description="تحكم كامل في سلوك النشر التلقائي دون إعادة نشر التطبيق. القيم الفعّالة تُطبّق على خط التوريد مباشرة."
      />
      {error && <p className="mb-3 text-brand-bright text-sm">{error}</p>}
      {msg && <p className="mb-3 text-sm text-green-500">{msg}</p>}

      <div className="space-y-3">
        {rules.map((r) => (
          <div key={r.key} className="card p-4">
            <div className="flex items-center justify-between gap-3 mb-2">
              <span className="font-bold text-sm">{r.label_ar || r.key}</span>
              <span className="badge border-edge text-ink-muted" dir="ltr">{r.key} · {r.value_type}</span>
            </div>
            <div className="flex gap-2">
              <input
                value={drafts[r.key] ?? ""}
                onChange={(e) => setDrafts((prev) => ({ ...prev, [r.key]: e.target.value }))}
                className="input flex-1"
                dir="ltr"
              />
              <button onClick={() => save(r.key)} className="btn-primary text-sm">
                حفظ
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
