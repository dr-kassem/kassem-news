"use client";

import { useState } from "react";
import { PUBLIC_API } from "@/lib/api";

export default function Newsletter() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [message, setMessage] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setState("loading");
    try {
      const res = await fetch(`${PUBLIC_API}/api/newsletter`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, language: "ar" }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "تعذر إتمام الاشتراك");
      setState("done");
      setMessage(data.message || "تم تسجيل اشتراكك بنجاح");
      setEmail("");
    } catch (err) {
      setState("error");
      setMessage(err instanceof Error ? err.message : "تعذر إتمام الاشتراك");
    }
  }

  return (
    <section className="bg-ink text-base">
      <div className="container-page grid gap-6 py-8 md:grid-cols-[1fr_1.2fr] md:items-center">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.25em] text-brand-bright">النشرة الإخبارية</p>
          <h2 className="mt-2 font-display text-3xl font-extrabold">صورة اليوم، في بريدك.</h2>
          <p className="mt-2 text-sm text-base/70">
            أهم عناوين الشرق الأوسط والعالم في رسالة واحدة، مرتين يومياً.
          </p>
        </div>
        <form onSubmit={submit} className="flex flex-col gap-3 sm:flex-row">
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="بريدك الإلكتروني"
            aria-label="البريد الإلكتروني"
            className="flex-1 rounded-md border border-base/25 bg-base/10 px-4 py-3 text-sm text-base placeholder:text-base/50 focus:border-brand-bright focus:outline-none"
          />
          <button type="submit" disabled={state === "loading"} className="btn-primary whitespace-nowrap bg-brand px-6">
            {state === "loading" ? "جارٍ التسجيل…" : "اشترك الآن"}
          </button>
        </form>
      </div>
      {message && (
        <div className="border-t border-base/15">
          <p className={`container-page py-2 text-xs ${state === "error" ? "text-brand-bright" : "text-base"}`}>
            {message}
          </p>
        </div>
      )}
    </section>
  );
}
