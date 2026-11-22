import Link from "next/link";
import type { Article } from "@/lib/types";

export default function MostRead({ articles }: { articles: Article[] }) {
  if (!articles.length) return null;
  return (
    <section className="paper-panel p-4">
      <p className="kicker mb-1">الأكثر تداولاً</p>
      <h2 className="mb-4 font-display text-xl font-extrabold text-ink">الأكثر قراءة</h2>
      <ol>
        {articles.map((a, i) => (
          <li key={a.id} className="flex gap-3 border-t border-edge py-3 first:border-0 first:pt-0">
            <span className="w-7 shrink-0 font-display text-3xl font-extrabold leading-none text-brand/40">
              {i + 1}
            </span>
            <Link href={`/article/${a.id}`} className="text-sm font-bold leading-snug hover:text-brand-bright line-clamp-2">
              {a.title_ar}
            </Link>
          </li>
        ))}
      </ol>
    </section>
  );
}
