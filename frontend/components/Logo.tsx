import Link from "next/link";

export default function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <Link href="/" className="group inline-flex select-none items-center gap-3" aria-label="قاسم نيوز - Kassem News">
      <span className="relative flex h-10 w-10 items-center justify-center border-2 border-brand">
        <span className="font-display text-xl font-extrabold text-brand">ق</span>
        <span className="absolute -left-1 -top-1 h-2 w-2 bg-brand" aria-hidden />
      </span>
      <span className="flex flex-col leading-none">
        <span className="font-display text-[26px] font-extrabold tracking-tight text-ink">
          قاسم <span className="text-brand">نيوز</span>
        </span>
        {!compact && (
          <span className="mt-1 border-t border-edge pt-0.5 text-[9px] font-semibold tracking-[0.32em] text-ink-muted">
            KASSEM NEWS
          </span>
        )}
      </span>
    </Link>
  );
}
