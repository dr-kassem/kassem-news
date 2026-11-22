import ArticleCard from "@/components/ArticleCard";
import EmptyState from "@/components/EmptyState";
import PageHero from "@/components/PageHero";
import { api } from "@/lib/api";
import type { Article } from "@/lib/types";

export const revalidate = 300;

export const metadata = {
  title: "في مثل هذا اليوم",
  description: "أخبار وتطورات وقعت في مثل هذا اليوم من أعوام سابقة، على قاسم نيوز.",
  alternates: { canonical: "/on-this-day" },
};

export default async function OnThisDayPage() {
  const items = (await api.onThisDay()) ?? [];
  const now = new Date();
  const day = now.toLocaleDateString("ar-SA", { day: "numeric" });
  const month = now.toLocaleDateString("ar-SA", { month: "long" });

  const byYear = items.reduce<Record<string, Article[]>>((acc, a) => {
    const year = String(new Date(a.published_at || a.source_published_at || "").getFullYear());
    if (!acc[year]) acc[year] = [];
    acc[year].push(a);
    return acc;
  }, {});
  const years = Object.keys(byYear).sort((a, b) => Number(b) - Number(a));

  return (
    <div>
      <PageHero
        kicker="أرشيف قاسم نيوز"
        title="في مثل هذا اليوم"
        description={`أخبار وتطورات وقعت في ${day} ${month} من أعوام سابقة، من أرشيف المنصة.`}
        meta={
          <>
            <span>{items.length} مادة أرشيفية</span>
            <span className="h-3 w-px bg-edge" aria-hidden />
            <span>{years.length} أعوام</span>
          </>
        }
      />

      <div className="mb-10 flex items-center gap-5 border-y-4 border-brand bg-surface/60 p-5">
        <div className="flex h-20 w-20 shrink-0 flex-col items-center justify-center border-2 border-brand bg-card">
          <span className="font-display text-3xl font-extrabold leading-none text-brand">{day}</span>
          <span className="mt-1 text-[11px] font-bold text-ink-muted">{month}</span>
        </div>
        <div>
          <p className="kicker">محطة في الأرشيف</p>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-muted">
            نستعرض ما نشرناه في هذا اليوم من سنوات مضيّة، لنرى كيف تطورت التغطية وتغيّرت التفاصيل.
          </p>
        </div>
      </div>

      {items.length ? (
        <div className="space-y-12">
          {years.map((year) => (
            <section key={year} className="grid gap-5 lg:grid-cols-[120px_1fr]">
              <div className="border-r-4 border-brand pr-4">
                <p className="font-display text-4xl font-extrabold text-ink">{year}</p>
                <p className="mt-1 text-xs text-ink-muted">{byYear[year].length} أخبار</p>
              </div>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {byYear[year].map((a) => (
                  <ArticleCard key={a.id} article={a} />
                ))}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <EmptyState
          title="لا توجد أحداث في مثل هذا اليوم"
          message="لم يُسجَّل أي خبر في مثل هذا اليوم من أعوام سابقة بعد."
          actionHref="/"
          actionLabel="العودة للرئيسية"
        />
      )}
    </div>
  );
}
