"use client";

import { useState } from "react";

export default function ShareControls({ title, url }: { title: string; url: string }) {
  const [copied, setCopied] = useState(false);
  const fullUrl = typeof window !== "undefined" ? new URL(url, window.location.origin).toString() : url;
  const encoded = encodeURIComponent(fullUrl);
  const text = encodeURIComponent(title);

  const targets = [
    { label: "X", href: `https://twitter.com/intent/tweet?text=${text}&url=${encoded}` },
    { label: "فيسبوك", href: `https://www.facebook.com/sharer/sharer.php?u=${encoded}` },
    { label: "واتساب", href: `https://wa.me/?text=${text}%20${encoded}` },
    { label: "تيليجرام", href: `https://t.me/share/url?url=${encoded}&text=${text}` },
  ];

  async function copy() {
    try {
      await navigator.clipboard.writeText(fullUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs text-ink-muted">مشاركة:</span>
      {targets.map((t) => (
        <a
          key={t.label}
          href={t.href}
          target="_blank"
          rel="noopener noreferrer"
          className="badge border-edge text-ink-muted hover:text-ink hover:border-brand transition-colors"
        >
          {t.label}
        </a>
      ))}
      <button onClick={copy} className="badge border-edge text-ink-muted hover:text-ink hover:border-brand transition-colors">
        {copied ? "تم النسخ" : "نسخ الرابط"}
      </button>
    </div>
  );
}
