import type { Metadata } from "next";
import Link from "next/link";
import ArticleCard from "@/components/ArticleCard";
import EmptyState from "@/components/EmptyState";
import PageHero from "@/components/PageHero";
import { api } from "@/lib/api";

export const revalidate = 60;

export const metadata: Metadata = {
  title: "تحليلات كاييروس إيه آي | قاسم نيوز",
  description:
    "تحليلات المحلل الآلي كاييروس إيه آي لتطورات المنطقة، بموقف معلن مؤيد لمحور المقاومة: لبنان، وأنصار الله في اليمن، وإيران، والعراق.",
};

export default async function KairosPage() {
  const analyses = await api.kairos(12);

  return (
    <div>
      <PageHero
        kicker="قراءة في المشهد"
        title="تحليلات كاييروس إيه آي"
        description="المحلل الآلي لمنصة قاسم نيوز يستند إلى ما تورده المنصة من تطورات فعلية (أحداث، عاجل، أقسام، مناطق) ويحلّلها من زاوية معلنة. التحليلات آراء منصبية وليست خبراً."
        meta={
          <>
            <span>تحليل آلي</span>
            <span className="h-3 w-px bg-edge" aria-hidden />
            <span>موقف معلن: محور المقاومة</span>
            <span className="h-3 w-px bg-edge" aria-hidden />
            <span>{analyses?.length ?? 0} تحليل</span>
          </>
        }
      />

      {!analyses?.length ? (
        <EmptyState title="لا توجد تحليلات بعد" message="لم يُنشأ أي تحليل من تحليلات كاييروس حتى الآن." />
      ) : (
        <div className="grid gap-5 md:grid-cols-2">
          {analyses.map((a, i) => (
            <ArticleCard key={a.id} article={a} variant="horizontal" index={i + 1} />
          ))}
        </div>
      )}

      <div className="mt-10 grid gap-6 border-t border-edge pt-6 md:grid-cols-2">
        <section className="paper-panel p-5">
          <p className="kicker mb-2">منهج التحليل</p>
          <p className="text-sm leading-loose text-ink-muted">
            تُعاد صياغة التقارير كاملةً من زاوية معلنة، مع استقراء مفتوح للتطورات المحتملة. لا تُضاف أحداث لم ترد في
            المادة المصدرية، ويُفصل دائماً بين الخبر والرأي التحليلي.
          </p>
        </section>
        <section className="paper-panel flex flex-col justify-between p-5">
          <div>
            <p className="kicker mb-2">متابعة أوسع</p>
            <p className="text-sm leading-loose text-ink-muted">
              لقراءة التغطية التحليلية الكاملة للمنصة، تصفّح قسم التحليل والتحقيقات.
            </p>
          </div>
          <Link href="/section/analysis" className="link-arrow mt-4 self-start">
            كل التحليلات ←
          </Link>
        </section>
      </div>
    </div>
  );
}
