import Link from "next/link";
import type { Article } from "@/lib/types";

export default function BreakingTicker({ items }: { items: Article[] }) {
  if (!items.length) return null;
  const feed = items.slice(0, 8);
  return (
    <div className="border-b border-breaking/30 bg-breaking text-white">
      <div className="container-page flex items-stretch">
        <div className="flex shrink-0 items-center gap-2 border-l border-white/25 px-4 py-2">
          <span className="inline-block h-2 w-2 rounded-full bg-white animate-pulse" aria-hidden />
          <span className="text-sm font-extrabold tracking-wide">عاجل</span>
        </div>
        <div className="relative flex-1 overflow-hidden py-2">
          <div className="ticker-track">
            {[...feed, ...feed].map((a, i) => (
              <Link
                key={`${a.id}-${i}`}
                href={`/article/${a.id}`}
                className="mx-6 inline-flex items-center gap-2 text-[13px] font-semibold hover:underline"
              >
                <span className="h-1 w-1 rounded-full bg-white/70" aria-hidden />
                <span className="text-white/70">{a.source?.name_ar}</span>
                <span>{a.title_ar}</span>
              </Link>
            ))}
          </div>
        </div>
        <Link href="/breaking" className="hidden shrink-0 items-center border-r border-white/25 px-4 text-xs font-bold sm:flex">
          كل العناوين
        </Link>
      </div>
    </div>
  );
}
