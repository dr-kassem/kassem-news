import type { Metadata } from "next";
import Link from "next/link";
import EmptyState from "@/components/EmptyState";
import PageHero from "@/components/PageHero";
import Pagination from "@/components/Pagination";
import StrikesMap from "@/components/StrikesMap";
import { api } from "@/lib/api";
import { fullDate, timeAgo } from "@/lib/format";
import type { StrikeReport } from "@/lib/types";

export const revalidate = 60;

export const metadata: Metadata = {
  title: "الغارات",
  description:
    "رصد ميداني مباشر للغارات الجوية والقصف المدفعي والمسيّرات والاستهدافات، محدّث لحظياً على قاسم نيوز.",
  alternates: { canonical: "/strikes" },
};

function mapsUrl(report: StrikeReport): string | null {
  if (typeof report.lat !== "number" || typeof report.lon !== "number") return null;
  return `https://www.google.com/maps?q=${report.lat},${report.lon}`;
}

function ReportCard({ report }: { report: StrikeReport }) {
  const map = mapsUrl(report);
  return (
    <li className="relative pr-6">
      <span className="absolute right-0 top-6 h-3 w-3 rounded-full border-2 border-base bg-brand" aria-hidden />
      <article className="card card-hover p-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="flex flex-wrap gap-1.5">
            <span className="badge border-breaking/50 bg-breaking/10 text-breaking-bright">{report.type_label}</span>
            <span className="badge border-edge text-ink-muted">{report.category}</span>
          </div>
          <time className="whitespace-nowrap text-[11px] text-ink-muted" dateTime={report.created_at} title={fullDate(report.created_at)}>
            {timeAgo(report.created_at)}
          </time>
        </div>
        <h3 className="mt-3 font-display text-lg font-extrabold leading-snug">
          {report.city_name || "موقع غير محدّد"}
        </h3>
        {report.description && (
          <p className="mt-2 text-sm leading-relaxed text-ink-muted">{report.description}</p>
        )}
        <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-edge pt-3 text-[11px] text-ink-muted">
          {report.evidence_label && <span>{report.evidence_label}</span>}
          <span className="font-bold">المصدر: قاسم نيوز</span>
          {map && (
            <Link href={map} target="_blank" rel="noopener noreferrer" className="link-arrow mr-auto text-[11px]">
              على الخريطة ↗
            </Link>
          )}
        </div>
      </article>
    </li>
  );
}

export default async function StrikesPage({
  searchParams,
}: {
  searchParams: Promise<{ type?: string; page?: string }>;
}) {
  const { type, page } = await searchParams;
  const active = type || "";
  const currentPage = Math.max(1, Number(page) || 1);

  const data = await api.strikes({ type: active || undefined, page: currentPage, page_size: 12 });
  const items = data?.items ?? [];
  const types = data?.types ?? [];
  const total = data?.total ?? 0;
  const updated = data?.updated_at ?? null;
  const baseHref = active ? `/strikes?type=${active}` : "/strikes";
  const allTypes = types.reduce((sum, t) => sum + t.count, 0);
  const located = items.filter((r) => typeof r.lat === "number" && typeof r.lon === "number").length;

  return (
    <div>
      <PageHero
        kicker="الرصد الميداني"
        title="خريطة الغارات"
        tone="live"
        description="رصد ميداني مباشر للغارات الجوية والقصف المدفعي والمسيّرات والاستهدافات، محدّث لحظياً. تُعرض البلاغات مرتّبة من الأحدث."
        meta={
          <>
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" aria-hidden />
              مباشر
            </span>
            <span className="h-3 w-px bg-edge" aria-hidden />
            {updated && <span>آخر تحديث {timeAgo(updated)}</span>}
            <span className="h-3 w-px bg-edge" aria-hidden />
            <span>{total} بلاغ</span>
          </>
        }
      />

      <div className="mb-8 grid gap-3 sm:grid-cols-3">
        <div className="stat-tile">
          <p className="text-[11px] font-bold text-ink-muted">إجمالي البلاغات</p>
          <p className="mt-1 font-display text-3xl font-extrabold text-ink">{total}</p>
        </div>
        <div className="stat-tile">
          <p className="text-[11px] font-bold text-ink-muted">أنواع الاستهداف</p>
          <p className="mt-1 font-display text-3xl font-extrabold text-ink">{types.length}</p>
        </div>
        <div className="stat-tile">
          <p className="text-[11px] font-bold text-ink-muted">مواقع محدّدة في هذه الصفحة</p>
          <p className="mt-1 font-display text-3xl font-extrabold text-ink">{located}</p>
        </div>
      </div>

      {types.length > 0 && (
        <div className="mb-8 flex flex-wrap gap-2 border-y border-edge py-3">
          <Link href="/strikes" className={`chip ${active === "" ? "chip-active" : ""}`}>
            الكل ({allTypes})
          </Link>
          {types.map((t) => (
            <Link key={t.type} href={`/strikes?type=${t.type}`} className={`chip ${active === t.type ? "chip-active" : ""}`}>
              {t.label} ({t.count})
            </Link>
          ))}
        </div>
      )}

      {items.length ? (
        <>
          <div className="grid gap-8 lg:grid-cols-12">
            <div className="lg:col-span-5">
              <div className="lg:sticky lg:top-44">
                <StrikesMap items={items} />
              </div>
            </div>
            <div className="lg:col-span-7">
              <div className="section-title mb-5">
                <h2>سجل البلاغات</h2>
                <span className="text-[11px] text-ink-muted">الأحدث أولاً</span>
              </div>
              <ol className="space-y-5 border-r border-edge pr-4">
                {items.map((report) => (
                  <ReportCard key={report.id} report={report} />
                ))}
              </ol>
            </div>
          </div>
          <Pagination page={currentPage} pages={data?.pages ?? 1} baseHref={baseHref} />
        </>
      ) : (
        <EmptyState
          title="لا توجد غارات مرصودة حالياً"
          message="لم تُسجَّل غارات أو قصف أو استهدافات جديدة خلال الفترة الأخيرة."
          actionHref="/"
          actionLabel="العودة للرئيسية"
        />
      )}
    </div>
  );
}
