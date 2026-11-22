import Link from "next/link";

export default function EmptyState({
  title = "لا توجد أخبار منشورة بعد",
  message = "لم تُنشر أي أخبار حتى الآن. يُجمع المحتوى تلقائياً من المصادر المعتمدة.",
  actionHref,
  actionLabel,
}: {
  title?: string;
  message?: string;
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <div className="border-y border-edge bg-surface/40 px-6 py-14 text-center">
      <div className="mx-auto flex h-12 w-12 items-center justify-center border border-brand/40 font-display text-2xl font-extrabold text-brand">
        —
      </div>
      <h3 className="mt-4 font-display text-xl font-extrabold text-ink">{title}</h3>
      <p className="mx-auto mt-2 max-w-lg text-sm leading-relaxed text-ink-muted">{message}</p>
      {actionHref && actionLabel && (
        <Link href={actionHref} className="btn-ghost mt-5 inline-flex">
          {actionLabel}
        </Link>
      )}
    </div>
  );
}
