import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import ArticleCard from "@/components/ArticleCard";
import ListenButton from "@/components/ListenButton";
import Reactions from "@/components/Reactions";
import ReadingProgress from "@/components/ReadingProgress";
import ShareControls from "@/components/ShareControls";
import { api } from "@/lib/api";
import { fullDate, timeAgo, VERIFICATION_LABELS, VERIFICATION_STYLES } from "@/lib/format";

export const revalidate = 60;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const article = await api.article(id);
  if (!article) return { title: "المقال غير موجود" };
  return {
    title: article.title_ar,
    description: article.summary_ar || article.title_ar,
    alternates: { canonical: `/article/${article.id}` },
    openGraph: {
      type: "article",
      title: article.title_ar,
      description: article.summary_ar,
      images: article.image_url ? [article.image_url] : undefined,
      publishedTime: article.published_at || undefined,
      modifiedTime: article.updated_at,
    },
  };
}

export default async function ArticlePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const article = await api.article(id);
  if (!article) notFound();

  const paragraphs = (article.body_ar || article.summary_ar || "")
    .split(/\n{2,}/)
    .map((p) => p.trim())
    .filter(Boolean);
  const wordCount = paragraphs.join(" ").split(/\s+/).filter(Boolean).length;
  const readMinutes = Math.max(1, Math.round(wordCount / 200));

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    headline: article.title_ar,
    articleSection: article.category?.name_ar,
    datePublished: article.published_at || article.source_published_at,
    dateModified: article.updated_at,
    image: article.image_url ? [article.image_url] : undefined,
    video: article.video_url
      ? {
          "@type": "VideoObject",
          name: article.title_ar,
          contentUrl: article.video_url,
          uploadDate: article.published_at || article.updated_at,
        }
      : undefined,
    author: article.author
      ? { "@type": "Person", name: article.author }
      : { "@type": "Organization", name: "قاسم نيوز" },
    publisher: { "@type": "Organization", name: "قاسم نيوز" },
    isAccessibleForFree: true,
    description: article.summary_ar,
  };

  return (
    <article>
      <ReadingProgress />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />

      <nav className="mb-5 flex items-center gap-2 border-b border-edge pb-3 text-xs text-ink-muted">
        <Link href="/" className="hover:text-brand-bright">الرئيسية</Link>
        <span aria-hidden>/</span>
        {article.category ? (
          <>
            <Link href={`/section/${article.category.slug}`} className="hover:text-brand-bright">
              {article.category.name_ar}
            </Link>
            <span aria-hidden>/</span>
          </>
        ) : null}
        <span className="line-clamp-1 text-ink">{article.title_ar}</span>
      </nav>

      <header className="mx-auto max-w-4xl">
        <div className="flex flex-wrap items-center gap-1.5">
          {article.is_breaking && <span className="badge border-breaking bg-breaking text-white">عاجل</span>}
          {article.category && (
            <Link href={`/section/${article.category.slug}`} className="badge border-brand/40 bg-brand/10 text-brand-bright">
              {article.category.name_ar}
            </Link>
          )}
          <span className={`badge ${VERIFICATION_STYLES[article.verification_status]}`}>
            {VERIFICATION_LABELS[article.verification_status]}
          </span>
        </div>
        <h1 className="mt-4 font-display text-4xl font-extrabold leading-[1.15] tracking-tight text-ink sm:text-5xl">
          {article.title_ar}
        </h1>
        {article.summary_ar && (
          <p className="mt-4 border-r-4 border-brand pr-4 text-lg leading-loose text-ink-muted">{article.summary_ar}</p>
        )}
        <div className="mt-6 flex flex-wrap items-center gap-x-4 gap-y-1 border-y border-edge py-3 text-xs text-ink-muted">
          <span className="font-bold text-ink">{article.author || "قاسم نيوز"}</span>
          <span className="h-3 w-px bg-edge" aria-hidden />
          {article.region && (
            <>
              <Link href={`/region/${article.region.slug}`} className="hover:text-brand-bright">
                {article.region.name_ar}
              </Link>
              <span className="h-3 w-px bg-edge" aria-hidden />
            </>
          )}
          <time dateTime={article.published_at || article.updated_at}>
            {fullDate(article.published_at || article.source_published_at)}
          </time>
          <span className="h-3 w-px bg-edge" aria-hidden />
          <span>{readMinutes} دقيقة قراءة</span>
          {article.updated_at && article.published_at && (
            <>
              <span className="h-3 w-px bg-edge" aria-hidden />
              <span>آخر تحديث {timeAgo(article.updated_at)}</span>
            </>
          )}
        </div>
      </header>

      {article.video_url && (
        <figure className="mt-8">
          <video
            src={article.video_url}
            controls
            playsInline
            preload="metadata"
            poster={article.image_url || undefined}
            className="aspect-video w-full border border-edge bg-black"
          >
            متصفحك لا يدعم تشغيل الفيديو.
          </video>
        </figure>
      )}

      {article.image_url && (
        <figure className="mt-8 border-b-4 border-brand">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={article.image_url} alt={article.title_ar} className="max-h-[560px] w-full object-cover" />
        </figure>
      )}

      <div className="mt-8 grid gap-10 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <div className="article-body mx-auto max-w-3xl">
            {paragraphs.length ? (
              paragraphs.map((p, i) => <p key={i}>{p}</p>)
            ) : (
              <p>{article.summary_ar || "لا يتوافر نص إضافي لهذا الخبر."}</p>
            )}
          </div>

          <div className="mx-auto mt-8 max-w-3xl border-t border-edge pt-4 text-xs leading-relaxed text-ink-muted">
            هذا الخبر مُصنّف كـ«{VERIFICATION_LABELS[article.verification_status]}». لا تُعدّ التقارير المنقولة عن
            مصدر أو تلك قيد التطور تأكيداً مستقلاً من المنصة حتى تكتمل عملية التحقق التحريري.
          </div>
        </div>

        <aside className="lg:col-span-4">
          <div className="space-y-4 lg:sticky lg:top-44">
            <section className="paper-panel p-4">
              <p className="kicker mb-3">أدوات القارئ</p>
              <div className="flex flex-wrap items-center gap-2">
                <ListenButton text={`${article.title_ar}. ${paragraphs.join(" ")}`} />
                <Reactions articleId={article.id} />
              </div>
              <div className="mt-4 border-t border-edge pt-4">
                <ShareControls title={article.title_ar} url={`/article/${article.id}`} />
              </div>
            </section>

            {article.related.length > 0 && (
              <section className="card p-4">
                <p className="kicker mb-1">اقرأ أيضاً</p>
                <div className="section-title mb-2">
                  <h2>أخبار ذات صلة</h2>
                </div>
                {article.related.map((a, i) => (
                  <ArticleCard key={a.id} article={a} variant="compact" index={i + 1} />
                ))}
              </section>
            )}
          </div>
        </aside>
      </div>

      {article.related.length >= 3 && (
        <section className="mt-14 border-t border-edge pt-8">
          <div className="section-title mb-5">
            <h2>المزيد من التغطية</h2>
            <Link href="/" className="link-arrow">الرئيسية ←</Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {article.related.slice(0, 3).map((a) => (
              <ArticleCard key={a.id} article={a} />
            ))}
          </div>
        </section>
      )}
    </article>
  );
}
