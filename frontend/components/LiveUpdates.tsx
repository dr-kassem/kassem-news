import Link from "next/link";
import type { Article, EventItem } from "@/lib/types";
import { timeAgo } from "@/lib/format";

export default function LiveUpdates({ events, latest }: { events: EventItem[]; latest: Article[] }) {
  return (
    <section className="card p-4">
      <div className="flex items-center justify-between border-b border-edge pb-3">
        <div>
          <p className="kicker mb-1">الرصد المباشر</p>
          <h2 className="font-display text-xl font-extrabold text-ink">متابعة حيّة</h2>
        </div>
        <span className="flex items-center gap-1.5 text-[11px] font-bold text-brand-bright">
          <span className="h-1.5 w-1.5 rounded-full bg-brand-bright animate-pulse" aria-hidden />
          مباشر
        </span>
      </div>

      {events.length > 0 && (
        <ul className="mt-4 space-y-3">
          {events.slice(0, 3).map((e) => (
            <li key={e.id} className="border-r-2 border-brand pr-3">
              <Link href={`/event/${e.id}`} className="block hover:text-brand-bright">
                <div className="mb-1 flex items-center gap-2 text-[11px] text-ink-muted">
                  {e.is_developing && <span className="badge border-brand/50 bg-brand/10 text-brand-bright">قيد التطور</span>}
                  <span>{e.article_count} تحديث</span>
                  <span aria-hidden>•</span>
                  <time>{timeAgo(e.last_update_at)}</time>
                </div>
                <p className="text-sm font-bold leading-snug line-clamp-2">{e.title_ar}</p>
              </Link>
            </li>
          ))}
        </ul>
      )}

      <h3 className="mt-6 border-b border-edge pb-2 text-xs font-bold uppercase tracking-wider text-ink-muted">
        أحدث الأخبار
      </h3>
      <ol className="mt-2">
        {latest.slice(0, 6).map((a, i) => (
          <li key={a.id} className="flex gap-3 border-b border-edge/60 py-2 text-sm last:border-0">
            <span className="w-4 shrink-0 font-bold text-brand">{i + 1}</span>
            <Link href={`/article/${a.id}`} className="line-clamp-2 hover:text-brand-bright">
              {a.title_ar}
            </Link>
          </li>
        ))}
      </ol>
    </section>
  );
}
