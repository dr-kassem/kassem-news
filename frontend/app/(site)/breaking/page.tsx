import type { Metadata } from "next";
import ArticleCard from "@/components/ArticleCard";
import EmptyState from "@/components/EmptyState";
import PageHero from "@/components/PageHero";
import Pagination from "@/components/Pagination";
import { api } from "@/lib/api";

export const revalidate = 60;

export const metadata: Metadata = {
  title: "أخبار عاجلة",
  description: "أحدث الأخبار العاجلة على قاسم نيوز.",
  alternates: { canonical: "/breaking" },
};

export default async function BreakingPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const { page } = await searchParams;
  const currentPage = Math.max(1, Number(page) || 1);
  const data = await api.articles({ breaking: true, page: currentPage, page_size: 12 });
  const items = data?.items ?? [];
  const [first, ...rest] = items;

  return (
    <div>
      <PageHero
        kicker="الأخبار العاجلة"
        title="عاجل"
        tone="breaking"
        description="الأخبار العاجلة تُراجع تحريرياً قبل النشر. تُعرض هنا الأخبار المصنّفة كعاجلة بعد اعتمادها."
        meta={
          <>
            <span>{data?.total ?? 0} خبر عاجل</span>
            <span className="h-3 w-px bg-edge" aria-hidden />
            <span>تحديث كل دقيقة</span>
          </>
        }
      />

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
          <Pagination page={currentPage} pages={data?.pages ?? 1} baseHref="/breaking" />
        </>
      ) : (
        <EmptyState
          title="لا توجد أخبار عاجلة معتمدة حالياً"
          message="لا توجد أخبار عاجلة منشورة في الوقت الحالي."
          actionHref="/"
          actionLabel="العودة للرئيسية"
        />
      )}
    </div>
  );
}
