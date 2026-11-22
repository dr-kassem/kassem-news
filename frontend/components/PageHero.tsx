import type { ReactNode } from "react";
import Link from "next/link";

export default function PageHero({
  kicker,
  title,
  description,
  meta,
  actionHref,
  actionLabel,
  tone = "default",
}: {
  kicker?: string;
  title: string;
  description?: string;
  meta?: ReactNode;
  actionHref?: string;
  actionLabel?: string;
  tone?: "default" | "breaking" | "live";
}) {
  const titleColor = tone === "breaking" ? "text-breaking-bright" : "text-ink";

  return (
    <header className="mb-8 border-b border-edge">
      <div className="flex items-start justify-between gap-5">
        <div className="min-w-0">
          {kicker && <p className="kicker mb-2">{kicker}</p>}
          <h1 className={`font-display text-4xl font-extrabold leading-[1.12] tracking-tight sm:text-5xl ${titleColor}`}>
            {title}
          </h1>
          {description && (
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-ink-muted sm:text-base">{description}</p>
          )}
        </div>
        {actionHref && actionLabel && (
          <Link href={actionHref} className="chip mt-2 shrink-0">
            {actionLabel}
          </Link>
        )}
      </div>
      <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-edge pt-3 text-xs text-ink-muted">
        {meta ?? (
          <>
            <span>قاسم نيوز</span>
            <span className="h-3 w-px bg-edge" aria-hidden />
            <span>العالم في الصورة الكاملة</span>
          </>
        )}
      </div>
    </header>
  );
}
