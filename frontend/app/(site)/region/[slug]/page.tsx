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
  const regions = (await api.regions()) || [];
  const region = regions.find((r) => r.slug === slug);
  return {
    title: region ? `أخبار ${region.name_ar}` : "منطقة",
    description: `تغطية قاسم نيوز لأخبار ${region?.name_ar ?? slug}.`,
    alternates: { canonical: `/region/${slug}` },
  };
}

export default async function RegionPage({
  params,
  searchParams,
}: {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ page?: string }>;
}) {
  const { slug } = await params;
  const { page } = await searchParams;
  const currentPage = Math.max(1, Number(page) || 1);
  const regions = (await api.regions()) || [];
  const region = regions.find((r) => r.slug === slug);
  if (!region) notFound();

  const data = await api.articles({ region: slug, page: currentPage, page_size: 12 });
  const items = data?.items ?? [];
  const [first, ...rest] = items;

  return (
    <div>
      <PageHero
        kicker={`منطقة · ${region.name_en}`}
        title={region.name_ar}
        description={`رصد وتغطية قاسم نيوز للتطورات في ${region.name_ar}.`}
        meta={
          <>
            <span>{data?.total ?? 0} خبر</span>
            <span className="h-3 w-px bg-edge" aria-hidden />
            <span>صفحة {currentPage}</span>
          </>
        }
      />

      {regions.length > 0 && (
        <div className="mb-8 flex flex-wrap gap-2 border-y border-edge py-3">
          {regions.map((r) => (
            <Link key={r.id} href={`/region/${r.slug}`} className={`chip ${r.slug === slug ? "chip-active" : ""}`}>
              {r.name_ar}
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
          <Pagination page={currentPage} pages={data?.pages ?? 1} baseHref={`/region/${slug}`} />
        </>
      ) : (
        <EmptyState
          title="لا توجد أخبار لهذه المنطقة"
          message="لم تُنشر أخبار عن هذه المنطقة بعد."
          actionHref="/"
          actionLabel="العودة للرئيسية"
        />
      )}
    </div>
  );
}
