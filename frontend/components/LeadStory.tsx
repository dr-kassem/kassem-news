import Link from "next/link";
import type { Article } from "@/lib/types";
import { timeAgo, VERIFICATION_LABELS, VERIFICATION_STYLES } from "@/lib/format";

export default function LeadStory({ article }: { article: Article }) {
  return (
    <section className="card card-hover grid overflow-hidden lg:grid-cols-12">
      <Link
        href={`/article/${article.id}`}
        className="relative block min-h-[260px] overflow-hidden lg:col-span-7 lg:min-h-[420px]"
      >
        {article.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={article.image_url}
            alt={article.title_ar}
            className="h-full w-full object-cover transition-transform duration-500 hover:scale-[1.03]"
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-surface font-display text-3xl font-bold text-brand">
            قاسم نيوز
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
        <span className="absolute right-4 top-4 badge border-white/40 bg-black/40 text-white">الخبر الرئيسي</span>
      </Link>

      <div className="flex flex-col justify-center border-r border-edge p-6 lg:col-span-5 lg:p-9">
        <p className="kicker">التغطية الرئيسية</p>
        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          {article.category && (
            <Link href={`/section/${article.category.slug}`} className="badge border-brand/40 bg-brand/10 text-brand-bright">
              {article.category.name_ar}
            </Link>
          )}
          {article.is_breaking && <span className="badge border-breaking bg-breaking text-white">عاجل</span>}
          <span className={`badge ${VERIFICATION_STYLES[article.verification_status]}`}>
            {VERIFICATION_LABELS[article.verification_status]}
          </span>
        </div>
        <h2 className="mt-4 font-display text-3xl font-extrabold leading-[1.2] tracking-tight sm:text-4xl">
          <Link href={`/article/${article.id}`} className="hover:text-brand-bright">
            {article.title_ar}
          </Link>
        </h2>
        {article.summary_ar && (
          <p className="mt-4 text-sm leading-loose text-ink-muted sm:text-base">{article.summary_ar}</p>
        )}
        <div className="mt-5 flex flex-wrap items-center gap-2 border-t border-edge pt-4 text-xs text-ink-muted">
          {article.source && <span className="font-bold text-ink">{article.source.name_ar}</span>}
          <span aria-hidden>•</span>
          <time dateTime={article.published_at || article.updated_at}>
            {timeAgo(article.published_at || article.source_published_at)}
          </time>
        </div>
        <Link href={`/article/${article.id}`} className="btn-primary mt-6 self-start">
          اقرأ التقرير ←
        </Link>
      </div>
    </section>
  );
}
