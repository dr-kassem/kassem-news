"use client";

import { useEffect, useRef, useState } from "react";
import { assistant } from "@/lib/api";
import type { AIMessage } from "@/lib/types";

const SUGGESTIONS = [
  "ما آخر الأخبار الآن؟",
  "لخّص أهم التطورات في لبنان",
  "ما هو كاييروس؟",
];

const WELCOME =
  "مرحباً بك في قاسم نيوز. اسألني عن آخر الأخبار أو اطلب تلخيصاً أو توضيحاً، وسأجيبك اعتماداً على تغطية الموقع.";

type Availability = "unknown" | "ready" | "off";

export default function AssistantWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [availability, setAvailability] = useState<Availability>("unknown");

  const endRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending, error]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  useEffect(() => {
    if (open && availability === "unknown") {
      assistant
        .status()
        .then((status) => setAvailability(status.configured ? "ready" : "off"))
        .catch(() => setAvailability("ready"));
    }
  }, [open, availability]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  async function send(text?: string) {
    const content = (text ?? input).trim();
    if (!content || sending || availability === "off") return;

    const next: AIMessage[] = [...messages, { role: "user", content }];
    setMessages(next);
    setInput("");
    setError("");
    setSending(true);
    try {
      const result = await assistant.chat(next.slice(-8));
      setMessages([...next, { role: "assistant", content: result.reply }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "تعذّر إرسال الطلب. حاول لاحقاً.");
    } finally {
      setSending(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="افتح مساعد الذكاء الاصطناعي"
        aria-expanded={open}
        className={`fixed bottom-4 start-4 z-40 items-center gap-2 rounded-full bg-brand px-4 py-3 text-sm font-bold text-brand-fg shadow-lg shadow-black/25 transition-colors hover:bg-brand-bright ${
          open ? "hidden" : "flex"
        }`}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 3l1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M18.5 15.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8.8-2.2z" />
        </svg>
        مساعد الذكاء
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="مساعد قاسم نيوز"
          className="fixed bottom-4 start-4 z-50 flex h-[min(78vh,560px)] w-[calc(100vw-2rem)] max-w-sm flex-col overflow-hidden rounded-xl border border-edge bg-card shadow-2xl"
        >
          <div className="flex items-center justify-between gap-3 border-b border-edge bg-surface px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="grid h-9 w-9 place-items-center rounded-full bg-brand/15 text-brand-bright">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 3l1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3z" />
                </svg>
              </span>
              <div>
                <p className="text-sm font-bold leading-tight">مساعد قاسم نيوز</p>
                <p className="text-[11px] text-ink-muted">مدعوم بالذكاء الاصطناعي</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {messages.length > 0 && (
                <button
                  type="button"
                  onClick={() => {
                    setMessages([]);
                    setError("");
                  }}
                  aria-label="مسح المحادثة"
                  className="rounded-md p-1.5 text-ink-muted transition-colors hover:bg-surface hover:text-ink"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-4 w-4" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 7h16M9 7V5h6v2M7 7l1 13h8l1-13M10 11v5M14 11v5" />
                  </svg>
                </button>
              )}
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="إغلاق المساعد"
                className="rounded-md p-1.5 text-ink-muted transition-colors hover:bg-surface hover:text-ink"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 6l12 12M18 6L6 18" />
                </svg>
              </button>
            </div>
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto bg-bg p-3">
            {messages.length === 0 && (
              <div className="space-y-3">
                <div className="max-w-[92%] rounded-lg border border-edge bg-surface px-3 py-2 text-sm leading-relaxed text-ink">
                  {WELCOME}
                </div>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTIONS.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => send(suggestion)}
                      disabled={sending || availability === "off"}
                      className="rounded-full border border-edge px-3 py-1 text-xs text-ink-muted transition-colors hover:border-brand hover:text-ink disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {suggestion}
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
                    : "ml-auto border border-edge bg-surface text-ink"
                }`}
              >
                {message.content}
              </div>
            ))}

            {sending && (
              <div className="ml-auto max-w-[92%] rounded-lg border border-edge bg-surface px-3 py-2 text-sm text-ink-muted">
                يكتب…
              </div>
            )}

            {error && (
              <p className="rounded-md border border-brand/40 bg-brand/10 px-3 py-2 text-xs leading-relaxed text-brand-bright">
                {error}
              </p>
            )}
            <div ref={endRef} />
          </div>

          <div className="border-t border-edge bg-card p-3">
            {availability === "off" ? (
              <p className="text-xs leading-relaxed text-ink-muted">
                مساعد الذكاء الاصطناعي غير متاح حالياً. يمكنك متابعة آخر الأخبار من الصفحة الرئيسية.
              </p>
            ) : (
              <div className="flex items-end gap-2">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      send();
                    }
                  }}
                  rows={2}
                  maxLength={1200}
                  placeholder="اكتب سؤالك…"
                  aria-label="رسالتك إلى المساعد"
                  className="max-h-28 min-h-[44px] flex-1 resize-none rounded-md border border-edge bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-muted focus:border-brand focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => send()}
                  disabled={sending || !input.trim()}
                  aria-label="إرسال"
                  className="btn-primary h-11 px-3"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 3L10 14M21 3l-7 18-4-7-7-4 18-7z" />
                  </svg>
                </button>
              </div>
            )}
            <p className="mt-2 text-[10px] leading-relaxed text-ink-muted">
              مساعد آلي قد يخطئ؛ تحقّق من الأخبار المهمة من مصادرها.
            </p>
          </div>
        </div>
      )}
    </>
  );
}
