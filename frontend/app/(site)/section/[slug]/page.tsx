import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import ArticleCard from "@/components/ArticleCard";
import EmptyState from "@/components/EmptyState";
import PageHero from "@/components/PageHero";
import Pagination from "@/components/Pagination";
import { api } from "@/lib/api";

export const revalidate = 60;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const meta = await api.meta();
  const category = meta?.categories.find((c) => c.slug === slug);
  return {
    title: category ? `قسم ${category.name_ar}` : "قسم",
    description: `أحدث أخبار قسم ${category?.name_ar ?? slug} على قاسم نيوز.`,
    alternates: { canonical: `/section/${slug}` },
  };
}

export default async function SectionPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ page?: string }>;
}) {
  const { slug } = await params;
  const { page } = await searchParams;
  const currentPage = Math.max(1, Number(page) || 1);
  const meta = await api.meta();
  const category = meta?.categories.find((c) => c.slug === slug);
  if (!category) notFound();

  const data = await api.articles({ category: slug, page: currentPage, page_size: 12 });
  const items = data?.items ?? [];
  const [first, ...rest] = items;
  const sections = (meta?.categories ?? []).filter((c) => c.show_in_nav);

  return (
    <div>
      <PageHero
        kicker={`قسم · ${category.name_en}`}
        title={category.name_ar}
        description={`أحدث أخبار قسم ${category.name_ar} وتغطياته على قاسم نيوز.`}
        meta={
          <>
            <span>{data?.total ?? 0} خبر</span>
            <span className="h-3 w-px bg-edge" aria-hidden />
            <span>صفحة {currentPage}</span>
          </>
        }
      />

      {sections.length > 0 && (
        <div className="mb-8 flex flex-wrap gap-2 border-y border-edge py-3">
          {sections.map((c) => (
            <Link
              key={c.id}
              href={`/section/${c.slug}`}
              className={`chip ${c.slug === slug ? "chip-active" : ""}`}
            >
              {c.name_ar}
            </Link>
          ))}
        </div>
      )}

      {items.length ? (
        <>
          <ArticleCard article={first} variant="feature" />
          {rest.length > 0 && (
            <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {rest.map((a) => (
                <ArticleCard key={a.id} article={a} />
              ))}
            </div>
          )}
          <Pagination page={currentPage} pages={data?.pages ?? 1} baseHref={`/section/${slug}`} />
        </>
      ) : (
        <EmptyState
          title="لا توجد أخبار في هذا القسم"
          message="لم تُنشر أخبار في هذا القسم بعد."
          actionHref="/"
          actionLabel="العودة للرئيسية"
        />
      )}
    </div>
  );
}
