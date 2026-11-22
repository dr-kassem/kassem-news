"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function SearchBox({ className = "" }: { className?: string }) {
  const router = useRouter();
  const [value, setValue] = useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const q = value.trim();
    if (q) router.push(`/search?q=${encodeURIComponent(q)}`);
  }

  return (
    <form onSubmit={submit} role="search" className={`relative flex items-center ${className}`}>
      <svg
        aria-hidden
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        className="pointer-events-none absolute right-3 h-4 w-4 text-ink-muted"
      >
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" />
      </svg>
      <input
        type="search"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="ابحث في الأخبار…"
        aria-label="بحث"
        className="w-full rounded-full border border-edge bg-surface py-2 pr-9 pl-[74px] text-sm text-ink placeholder:text-ink-muted/70 focus:border-brand focus:outline-none"
      />
      <button
        type="submit"
        className="absolute left-1 rounded-full bg-brand px-3 py-1.5 text-xs font-bold text-brand-fg hover:bg-brand-bright"
        aria-label="تنفيذ البحث"
      >
        بحث
      </button>
    </form>
  );
}
