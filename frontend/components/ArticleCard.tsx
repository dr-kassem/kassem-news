import Link from "next/link";
import type { Article } from "@/lib/types";
import { timeAgo, VERIFICATION_LABELS, VERIFICATION_STYLES } from "@/lib/format";

function Thumb({ article, className = "" }: { article: Article; className?: string }) {
  if (article.image_url) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={article.image_url}
        alt={article.title_ar}
        loading="lazy"
        className={`object-cover w-full h-full ${className}`}
      />
    );
  }
  return (
    <div className={`flex items-center justify-center bg-surface font-display text-sm font-bold text-brand/60 ${className}`}>
      قاسم نيوز
    </div>
  );
}

function Badges({ article }: { article: Article }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {article.category && (
        <Link href={`/section/${article.category.slug}`} className="badge border-brand/40 bg-brand/10 text-brand-bright">
          {article.category.name_ar}
        </Link>
      )}
      {article.is_breaking && <span className="badge border-breaking bg-breaking text-white">عاجل</span>}
      {article.author?.startsWith("kairosAI") && (
        <span className="badge border-brand/40 bg-brand text-brand-fg">تحليل كاييروس AI</span>
      )}
      {article.verification_status !== "attributed" && (
        <span className={`badge ${VERIFICATION_STYLES[article.verification_status]}`}>
          {VERIFICATION_LABELS[article.verification_status]}
        </span>
      )}
    </div>
  );
}

function Meta({ article, light = false, staticRegion = false }: { article: Article; light?: boolean; staticRegion?: boolean }) {
  return (
    <div className={`flex flex-wrap items-center gap-x-2 gap-y-1 text-[12px] ${light ? "text-white/70" : "text-ink-muted"}`}>
      {article.source && <span className="font-bold">{article.source.name_ar}</span>}
      {article.region && (
        <>
          <span aria-hidden>•</span>
          {staticRegion ? (
            <span>{article.region.name_ar}</span>
          ) : (
            <Link href={`/region/${article.region.slug}`} className={light ? "hover:text-white" : "hover:text-ink"}>
              {article.region.name_ar}
            </Link>
          )}
        </>
      )}
      <span aria-hidden>•</span>
      <time dateTime={article.published_at || article.updated_at}>
        {timeAgo(article.published_at || article.source_published_at)}
      </time>
    </div>
  );
}

export default function ArticleCard({
  article,
  variant = "default",
  index,
}: {
  article: Article;
  variant?: "default" | "compact" | "horizontal" | "feature";
  index?: number;
}) {
  const href = `/article/${article.id}`;

  if (variant === "compact") {
    return (
      <article className="flex items-start gap-3 border-b border-edge py-3 last:border-0">
        {typeof index === "number" && (
          <span className="flex h-6 w-6 shrink-0 items-center justify-center border border-edge bg-surface text-[11px] font-bold text-brand">
            {index}
          </span>
        )}
        <div className="min-w-0">
          <h3 className="text-[14px] font-bold leading-snug">
            <Link href={href} className="line-clamp-2 hover:text-brand-bright">
              {article.title_ar}
            </Link>
          </h3>
          <div className="mt-1.5">
            <Meta article={article} />
          </div>
        </div>
      </article>
    );
  }

  if (variant === "horizontal") {
    return (
      <article className="card card-hover flex gap-4 p-3">
        <div className="h-24 w-28 shrink-0 overflow-hidden rounded">
          <Thumb article={article} />
        </div>
        <div className="min-w-0 flex-1">
          <Badges article={article} />
          <h3 className="mt-2 text-[15px] font-bold leading-snug line-clamp-2">
            <Link href={href} className="hover:text-brand-bright">
              {article.title_ar}
            </Link>
          </h3>
          <div className="mt-2">
            <Meta article={article} />
          </div>
        </div>
        {typeof index === "number" && (
          <span className="hidden self-start font-display text-2xl font-extrabold text-brand/40 sm:block">{index}</span>
        )}
      </article>
    );
  }

  if (variant === "feature") {
    return (
      <article className="card card-hover group overflow-hidden">
        <Link href={href} className="relative block aspect-[16/9] overflow-hidden">
          <Thumb article={article} className="group-hover:scale-[1.03] transition-transform duration-500" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent" />
          <div className="absolute bottom-0 right-0 left-0 p-5 sm:p-6">
            <div className="mb-3 flex flex-wrap items-center gap-1.5">
              {article.category && (
                <span className="badge border-brand bg-brand text-brand-fg">{article.category.name_ar}</span>
              )}
              {article.is_breaking && <span className="badge border-breaking bg-breaking text-white">عاجل</span>}
            </div>
            <h3 className="font-display text-2xl font-extrabold leading-tight text-white sm:text-3xl">
              {article.title_ar}
            </h3>
            {article.summary_ar && (
              <p className="mt-2 line-clamp-2 text-sm text-white/80">{article.summary_ar}</p>
            )}
            <div className="mt-3">
              <Meta article={article} light staticRegion />
            </div>
          </div>
        </Link>
      </article>
    );
  }

  return (
    <article className="card card-hover group flex flex-col overflow-hidden">
      <div className="h-1 w-full bg-brand" aria-hidden />
      <Link href={href} className="block aspect-[3/2] overflow-hidden">
        <Thumb article={article} className="group-hover:scale-[1.03] transition-transform duration-500" />
      </Link>
      <div className="flex flex-1 flex-col p-4">
        <Badges article={article} />
        <h3 className="mt-3 text-lg font-bold leading-snug line-clamp-3">
          <Link href={href} className="hover:text-brand-bright">
            {article.title_ar}
          </Link>
        </h3>
        {article.summary_ar && <p className="mt-2 text-sm leading-relaxed text-ink-muted line-clamp-2">{article.summary_ar}</p>}
        <div className="mt-4 border-t border-edge pt-3">
          <Meta article={article} />
        </div>
      </div>
    </article>
  );
}
