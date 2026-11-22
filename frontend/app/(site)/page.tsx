import Link from "next/link";
import ArticleCard from "@/components/ArticleCard";
import EmptyState from "@/components/EmptyState";
import LeadStory from "@/components/LeadStory";
import LiveUpdates from "@/components/LiveUpdates";
import MostRead from "@/components/MostRead";
import Newsletter from "@/components/Newsletter";
import SectionBlock from "@/components/SectionBlock";
import { api } from "@/lib/api";

export const revalidate = 60;

export default async function HomePage() {
  const [lead, latest, middleEast, lebanon, world, politics, economy, tech, events, mostRead, kairos] =
    await Promise.all([
      api.lead(),
      api.articles({ page_size: 12 }),
      api.articles({ region: "middle-east", page_size: 6 }),
      api.articles({ region: "lebanon", page_size: 6 }),
      api.articles({ category: "world", page_size: 6 }),
      api.articles({ category: "politics", page_size: 3 }),
      api.articles({ category: "economy", page_size: 3 }),
      api.articles({ category: "technology", page_size: 3 }),
      api.events(),
      api.mostRead(),
      api.kairos(4),
    ]);

  const latestItems = latest?.items ?? [];
  if (!lead && latestItems.length === 0) return <EmptyState />;

  const leadStory = lead ?? latestItems[0];
  const secondary = latestItems.filter((a) => a.id !== leadStory.id).slice(0, 4);
  const recentGrid = latestItems.filter((a) => a.id !== leadStory.id).slice(4, 12);

  return (
    <div className="space-y-12">
      <LeadStory article={leadStory} />

      {secondary.length > 0 && (
        <section>
          <div className="section-title mb-5">
            <h2>أهم العناوين</h2>
            <span className="text-[11px] text-ink-muted">تحديث مباشر</span>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {secondary.map((a, i) => (
              <ArticleCard key={a.id} article={a} variant="horizontal" index={i + 1} />
            ))}
          </div>
        </section>
      )}

      <div className="grid gap-8 lg:grid-cols-12">
        <div className="space-y-12 lg:col-span-8">
          <SectionBlock title="أحدث الأخبار" moreHref="/breaking" articles={recentGrid} grid={3} />
          <SectionBlock title="لبنان" moreHref="/region/lebanon" articles={lebanon?.items ?? []} grid={2} featureFirst />
          <SectionBlock
            title="الشرق الأوسط"
            moreHref="/region/middle-east"
            articles={middleEast?.items ?? []}
            grid={2}
          />
          <SectionBlock title="العالم" moreHref="/section/world" articles={world?.items ?? []} grid={2} />
        </div>

        <aside className="space-y-6 lg:col-span-4 lg:border-r lg:border-edge lg:pr-6">
          <LiveUpdates events={events ?? []} latest={latestItems} />
          {mostRead && mostRead.length > 0 && <MostRead articles={mostRead} />}
          {kairos && kairos.length > 0 && (
            <section className="paper-panel p-4">
              <p className="kicker mb-1">قراءة في المشهد</p>
              <div className="section-title mb-3">
                <h2>تحليلات كاييروس</h2>
              </div>
              {kairos.map((a) => (
                <ArticleCard key={a.id} article={a} variant="compact" />
              ))}
              <Link href="/kairos" className="link-arrow mt-4">
                كل التحليلات ←
              </Link>
            </section>
          )}
        </aside>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <SectionBlock title="سياسة" moreHref="/section/politics" articles={politics?.items ?? []} />
        <SectionBlock title="اقتصاد" moreHref="/section/economy" articles={economy?.items ?? []} />
        <SectionBlock title="تكنولوجيا" moreHref="/section/technology" articles={tech?.items ?? []} />
      </div>

      <Newsletter />
    </div>
  );
}
