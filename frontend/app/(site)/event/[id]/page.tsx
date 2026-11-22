import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import ArticleCard from "@/components/ArticleCard";
import PageHero from "@/components/PageHero";
import { api } from "@/lib/api";
import { fullDate, timeAgo } from "@/lib/format";

export const revalidate = 60;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const event = await api.event(id);
  if (!event) return { title: "الحدث غير موجود" };
  return { title: event.title_ar, description: event.summary_ar, alternates: { canonical: `/event/${id}` } };
}

export default async function EventPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const event = await api.event(id);
  if (!event) notFound();

  return (
    <div>
      <PageHero
        kicker="متابعة حدث"
        title={event.title_ar}
        description={event.summary_ar}
        meta={
          <>
            {event.is_developing && (
              <>
                <span className="badge border-brand/50 bg-brand/10 text-brand-bright">قيد التطور</span>
                <span className="h-3 w-px bg-edge" aria-hidden />
              </>
            )}
            <span>{event.article_count} تحديث</span>
            <span className="h-3 w-px bg-edge" aria-hidden />
            <span>بدأت المتابعة {fullDate(event.first_seen_at)}</span>
            <span className="h-3 w-px bg-edge" aria-hidden />
            <span>آخر تحديث {timeAgo(event.last_update_at)}</span>
          </>
        }
      />

      <div className="grid gap-8 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <div className="section-title mb-5">
            <h2>الخط الزمني للتطورات</h2>
            <span className="text-[11px] text-ink-muted">{event.timeline.length} محطات</span>
          </div>
          <ol className="space-y-6 border-r border-edge pr-6">
            {event.timeline.map((a, i) => (
              <li key={a.id} className="relative">
                <span className="absolute -right-[31px] top-5 h-3 w-3 rounded-full border-2 border-base bg-brand" aria-hidden />
                <span className="mb-2 inline-block text-[11px] font-bold text-brand-bright">المحطة {i + 1}</span>
                <ArticleCard article={a} variant="horizontal" />
              </li>
            ))}
          </ol>
        </div>

        <aside className="lg:col-span-4">
          <div className="space-y-4 lg:sticky lg:top-44">
            <section className="paper-panel p-5">
              <p className="kicker mb-2">ملاحظة تحريرية</p>
              <p className="text-sm leading-loose text-ink-muted">
                تجمع هذه الصفحة تحديثات الأخبار المتعلقة بالحدث نفسه من مصادر متعددة. قد تتعارض التقارير الأولية حتى
                تتم عملية التحقق.
              </p>
            </section>
            <Link href="/breaking" className="card-hover card block p-4">
              <p className="kicker mb-1">تغطية عاجلة</p>
              <p className="text-sm font-bold">تابع الأخبار العاجلة ←</p>
            </Link>
          </div>
        </aside>
      </div>
    </div>
  );
}
