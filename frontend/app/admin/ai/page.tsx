"use client";

import { useEffect, useRef, useState } from "react";
import AdminPageHeader from "@/components/AdminPageHeader";
import { admin } from "@/lib/api";
import type { AIEnrichResponse, AIMessage, AIStatus } from "@/lib/types";

const QUICK_PROMPTS = [
  "لخّص لي أهم التطورات في آخر الأخبار المنشورة.",
  "اقترح ثلاثة عناوين مهنية لخبر عاجل عن لبنان.",
  "ترجم هذا الخبر إلى العربية بأسلوب تحريري: ",
  "اقترح أسئلة تحقيق حول ملف اقتصادي إقليمي.",
];

export default function AIAssistantPage() {
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  const [articleId, setArticleId] = useState("");
  const [enrich, setEnrich] = useState<AIEnrichResponse | null>(null);
  const [enrichBusy, setEnrichBusy] = useState(false);
  const [enrichMsg, setEnrichMsg] = useState("");

  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    admin
      .aiStatus()
      .then(setStatus)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "تعذر قراءة حالة الذكاء الاصطناعي"),
      );
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  async function send() {
    const text = input.trim();
    if (!text || sending) return;
    const next: AIMessage[] = [...messages, { role: "user", content: text }];
    setMessages(next);
    setInput("");
    setSending(true);
    setError("");
    try {
      const result = await admin.aiChat(next);
      setMessages([...next, { role: "assistant", content: result.reply }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذر إرسال الطلب");
    } finally {
      setSending(false);
    }
  }

  async function runEnrich(apply: boolean) {
    const id = Number(articleId);
    if (!Number.isInteger(id) || id <= 0) {
      setEnrichMsg("أدخل رقم خبر صالحاً.");
      return;
    }
    setEnrichBusy(true);
    setEnrichMsg("");
    setEnrich(null);
    try {
      const result = await admin.aiEnrich(id, apply);
      setEnrich(result);
      setEnrichMsg(apply ? "تم تحسين الخبر وتطبيقه." : "هذه معاينة فقط، لم يُحفظ بعد.");
    } catch (err) {
      setEnrichMsg(err instanceof Error ? err.message : "تعذر تنفيذ الطلب");
    } finally {
      setEnrichBusy(false);
    }
  }

  const configured = status?.configured === true;

  return (
    <div>
      <AdminPageHeader
        title="مساعد الذكاء الاصطناعي"
        description="محادثة تحريرية سريعة وتحسين المقالات، مع معاينة قبل تطبيق أي تغيير."
        actions={
          <span
            className={`badge px-3 py-1 ${
              configured
                ? "border-emerald-700 bg-emerald-900/20 text-emerald-500"
                : "border-amber-800 bg-amber-900/20 text-amber-500"
            }`}
          >
            {configured ? `متصل — ${status?.model}` : "غير مهيّأ — أضف مفتاح OpenRouter"}
          </span>
        }
      />

      {status && !configured && (
        <div className="card p-4 text-sm text-ink-muted leading-relaxed">
          <p className="font-bold text-ink">لتفعيل الذكاء الاصطناعي:</p>
          <ol className="mt-2 list-decimal pr-5 space-y-1">
            <li>
              أنشئ مفتاحاً مجانياً من{" "}
              <a
                href="https://openrouter.ai/keys"
                target="_blank"
                rel="noreferrer"
                className="text-brand-bright hover:underline"
              >
                openrouter.ai/keys
              </a>
              .
            </li>
            <li>
              أضف في <code dir="ltr">backend/.env</code>:{" "}
              <code dir="ltr">OPENROUTER_API_KEY=sk-or-...</code>
            </li>
            <li>أعد تشغيل الخلفية. النموذج الافتراضي: {status.model}</li>
          </ol>
        </div>
      )}

      {error && <p className="text-brand-bright text-sm">{error}</p>}

      <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <section className="card flex h-[620px] flex-col p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-bold">المحادثة</h2>
            {messages.length > 0 && (
              <button onClick={() => setMessages([])} className="link-muted text-xs">
                مسح المحادثة
              </button>
            )}
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto rounded-md border border-edge bg-surface/60 p-3">
            {messages.length === 0 && (
              <div className="space-y-2">
                <p className="text-sm text-ink-muted">
                  اسأل عن الأخبار، اطلب تلخيصاً أو ترجمة أو صياغة عنوان.
                </p>
                <div className="flex flex-wrap gap-2">
                  {QUICK_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => setInput(prompt)}
                      className="rounded-full border border-edge px-3 py-1 text-xs text-ink-muted hover:border-brand hover:text-ink"
                    >
                      {prompt.length > 42 ? `${prompt.slice(0, 42)}…` : prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((message, index) => (
              <div
                key={index}
                className={`max-w-[92%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm leading-relaxed ${
                  message.role === "user"
                    ? "mr-auto bg-brand/15 text-ink"
                    : "ml-auto border border-edge bg-card text-ink"
                }`}
              >
                {message.content}
              </div>
            ))}
            {sending && (
              <div className="ml-auto max-w-[92%] rounded-lg border border-edge bg-card px-3 py-2 text-sm text-ink-muted">
                جارٍ التفكير…
              </div>
            )}
            <div ref={endRef} />
          </div>

          <div className="mt-3 flex items-end gap-2">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  send();
                }
              }}
              rows={2}
              placeholder="اكتب طلبك… (Enter للإرسال، Shift+Enter لسطر جديد)"
              className="min-h-[52px] flex-1 resize-none rounded-md border border-edge bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-muted focus:border-brand focus:outline-none"
            />
            <button
              onClick={send}
              disabled={sending || !input.trim() || !configured}
              className="btn-primary"
            >
              إرسال
            </button>
          </div>
        </section>

        <section className="card h-fit p-4">
          <h2 className="text-lg font-bold">تحسين خبر بالذكاء الاصطناعي</h2>
          <p className="mt-1 text-sm text-ink-muted">
            أدخل رقم الخبر لتلخيصه أو ترجمته إلى العربية. يمكنك المعاينة أولاً ثم التطبيق.
          </p>

          <label className="mt-4 block text-xs font-semibold text-ink-muted">رقم الخبر</label>
          <input
            dir="ltr"
            inputMode="numeric"
            value={articleId}
            onChange={(event) => setArticleId(event.target.value)}
            placeholder="مثال: 1234"
            className="mt-1 w-full rounded-md border border-edge bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-muted focus:border-brand focus:outline-none"
          />

          <div className="mt-3 flex flex-wrap gap-2">
            <button
              onClick={() => runEnrich(false)}
              disabled={enrichBusy || !configured}
              className="btn-ghost text-sm"
            >
              معاينة فقط
            </button>
            <button
              onClick={() => runEnrich(true)}
              disabled={enrichBusy || !configured}
              className="btn-primary text-sm"
            >
              {enrichBusy ? "جارٍ التنفيذ…" : "توليد وتطبيق"}
            </button>
          </div>

          {enrichMsg && <p className="mt-3 text-sm text-ink-muted">{enrichMsg}</p>}

          {enrich && (
            <div className="mt-4 space-y-2 rounded-md border border-edge bg-surface/60 p-3 text-sm">
              <div>
                <span className="text-xs text-ink-muted">العنوان المقترح</span>
                <p className="font-bold">{enrich.title_ar}</p>
              </div>
              <div>
                <span className="text-xs text-ink-muted">الملخص المقترح</span>
                <p className="leading-relaxed">{enrich.summary_ar}</p>
              </div>
              <p className="text-[11px] text-ink-muted" dir="ltr">
                model: {enrich.model}
              </p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
