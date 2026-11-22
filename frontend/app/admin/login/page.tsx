"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import Logo from "@/components/Logo";
import { admin, setToken } from "@/lib/api";

export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await admin.login(email, password);
      setToken(data.access_token);
      router.replace("/admin");
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر تسجيل الدخول");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-screen bg-base lg:grid-cols-2">
      <div className="hidden flex-col justify-between border-l-4 border-brand bg-ink p-12 text-base lg:flex">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center border-2 border-brand-bright font-display text-xl font-extrabold text-brand-bright">ق</span>
          <span className="font-display text-2xl font-extrabold">قاسم نيوز</span>
        </div>
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.3em] text-brand-bright">Kassem News</p>
          <h1 className="mt-4 max-w-md font-display text-5xl font-extrabold leading-tight">
            غرفة التحرير، في مكان واحد.
          </h1>
          <p className="mt-4 max-w-md text-sm leading-loose text-base/70">
            مراجعة الأخبار، إدارة المصادر، ضبط قواعد النشر، ومتابعة خط التوريد من واجهة واحدة.
          </p>
        </div>
        <p className="text-xs text-base/50">العالم في الصورة الكاملة</p>
      </div>

      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <Logo />
          </div>
          <p className="kicker mb-2">وصول مخصّص</p>
          <h2 className="font-display text-3xl font-extrabold text-ink">تسجيل الدخول</h2>
          <p className="mt-2 text-sm text-ink-muted">لوحة تحكم المحرّرين والمسؤولين.</p>
          <form onSubmit={submit} className="mt-8 space-y-4">
            <div>
              <label className="mb-1 block text-xs font-bold text-ink-muted" htmlFor="email">
                البريد الإلكتروني
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                dir="ltr"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-bold text-ink-muted" htmlFor="password">
                كلمة المرور
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                dir="ltr"
              />
            </div>
            {error && <p className="text-sm text-brand-bright">{error}</p>}
            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? "جارٍ الدخول…" : "دخول"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
