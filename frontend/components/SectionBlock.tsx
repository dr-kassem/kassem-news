import Link from "next/link";
import type { Article } from "@/lib/types";
import ArticleCard from "./ArticleCard";

export default function SectionBlock({
  title,
  moreHref,
  articles,
  grid = 3,
  featureFirst = false,
}: {
  title: string;
  moreHref?: string;
  articles: Article[];
  grid?: 2 | 3;
  featureFirst?: boolean;
}) {
  if (!articles.length) return null;
  const [first, ...rest] = articles;

  return (
    <section>
      <div className="section-title mb-5">
        <h2>{title}</h2>
        {moreHref && <Link href={moreHref} className="link-arrow">المزيد ←</Link>}
      </div>
      <div className={`grid gap-4 sm:grid-cols-2 ${grid === 3 ? "lg:grid-cols-3" : ""}`}>
        {featureFirst ? (
          <div className="sm:col-span-2 lg:col-span-3">
            <ArticleCard article={first} variant="feature" />
          </div>
        ) : (
          <ArticleCard article={first} />
        )}
        {rest.map((a) => (
          <ArticleCard key={a.id} article={a} />
        ))}
      </div>
    </section>
  );
}
