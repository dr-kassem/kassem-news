import type { Metadata } from "next";
import ArticleCard from "@/components/ArticleCard";
import EmptyState from "@/components/EmptyState";
import PageHero from "@/components/PageHero";
import Pagination from "@/components/Pagination";
import SearchBox from "@/components/SearchBox";
import { api } from "@/lib/api";

export const revalidate = 0;

export async function generateMetadata({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}): Promise<Metadata> {
  const { q } = await searchParams;
  return {
    title: q ? `نتائج البحث: ${q}` : "بحث",
    robots: { index: false, follow: true },
  };
}

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; page?: string }>;
}) {
  const { q, page } = await searchParams;
  const query = (q || "").trim();
  const currentPage = Math.max(1, Number(page) || 1);
  const data = query ? await api.articles({ q: query, page: currentPage, page_size: 12 }, 0) : null;
  const items = data?.items ?? [];

  return (
    <div>
      <PageHero
        kicker="البحث في الأرشيف"
        title="ابحث في الأخبار"
        description="ابحث في العناوين والملخصات والتغطيات المنشورة على قاسم نيوز."
      />

      <div className="paper-panel mb-8 p-4 sm:p-5">
        <SearchBox className="mx-auto max-w-2xl" />
      </div>

      {query ? (
        <>
          <div className="mb-5 flex flex-wrap items-center justify-between gap-2 border-b border-edge pb-3">
            <p className="text-sm text-ink-muted">
              نتائج البحث عن <span className="font-bold text-ink">«{query}»</span>
            </p>
            <p className="text-xs font-bold text-brand-bright">{data?.total ?? 0} نتيجة</p>
          </div>
          {items.length ? (
            <>
              <div className="grid gap-4 lg:grid-cols-2">
                {items.map((a, i) => (
                  <ArticleCard key={a.id} article={a} variant="horizontal" index={(currentPage - 1) * 12 + i + 1} />
                ))}
              </div>
              <Pagination page={currentPage} pages={data?.pages ?? 1} baseHref={`/search?q=${encodeURIComponent(query)}`} />
            </>
          ) : (
            <EmptyState
              title="لا توجد نتائج"
              message="لم نعثر على أخبار مطابقة لبحثك. جرّب كلمة أقصر أو مختلفة."
              actionHref="/"
              actionLabel="العودة للرئيسية"
            />
          )}
        </>
      ) : (
        <EmptyState
          title="ابدأ بكتابة كلمة بحث"
          message="أدخل كلمة للبحث في العناوين والملخصات."
          actionHref="/"
          actionLabel="العودة للرئيسية"
        />
      )}
    </div>
  );
}
