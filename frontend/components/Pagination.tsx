import Link from "next/link";

export default function Pagination({
  page,
  pages,
  baseHref,
}: {
  page: number;
  pages: number;
  baseHref: string;
}) {
  if (pages <= 1) return null;
  const sep = baseHref.includes("?") ? "&" : "?";
  const href = (p: number) => `${baseHref}${sep}page=${p}`;
  const numbers: number[] = [];
  for (let p = Math.max(1, page - 2); p <= Math.min(pages, page + 2); p++) numbers.push(p);

  return (
    <nav className="mt-8 flex flex-wrap items-center justify-center gap-2" aria-label="تنقل الصفحات">
      {page > 1 ? (
        <Link href={href(page - 1)} className="btn-ghost px-3 py-1.5">
          ← السابق
        </Link>
      ) : (
        <span className="btn-ghost px-3 py-1.5 opacity-40">← السابق</span>
      )}

      {numbers[0] > 1 && <span className="px-1 text-ink-muted">…</span>}
      {numbers.map((p) => (
        <Link
          key={p}
          href={href(p)}
          aria-current={p === page ? "page" : undefined}
          className={`h-9 w-9 border text-sm font-bold transition-colors ${
            p === page
              ? "border-brand bg-brand text-brand-fg"
              : "border-edge text-ink-muted hover:border-brand hover:text-ink"
          } flex items-center justify-center`}
        >
          {p}
        </Link>
      ))}
      {numbers[numbers.length - 1] < pages && <span className="px-1 text-ink-muted">…</span>}

      {page < pages ? (
        <Link href={href(page + 1)} className="btn-ghost px-3 py-1.5">
          التالي →
        </Link>
      ) : (
        <span className="btn-ghost px-3 py-1.5 opacity-40">التالي →</span>
      )}
      <span className="w-full text-center text-[11px] text-ink-muted">صفحة {page} من {pages}</span>
    </nav>
  );
}
