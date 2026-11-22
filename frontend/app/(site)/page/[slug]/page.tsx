import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import PageHero from "@/components/PageHero";

type PageContent = { title: string; body: string[] };

const PAGES: Record<string, PageContent> = {
  about: {
    title: "من نحن",
    body: [
      "قاسم نيوز منصة إخبارية رقمية تبني تجربة قراءة عربية حديثة، بشعار «العالم في الصورة الكاملة»، وتولي تغطيةً موسّعة للبنان والشرق الأوسط إلى جانب الأخبار الدولية.",
      "تعمل المنصة بنظام توريد أخبار آلي يستند إلى مصادر موثوقة معلنة، مع طبقة تحريرية للمراجعة والتدقيق، وترجمة الملخصات وتصنيفها حسب القسم والمنطقة والبلد.",
      "نلتزم بالشفافية والتمييز الواضح بين المعلومة المؤكدة والمعلومة المنقولة أو قيد التطور.",
    ],
  },
  contact: {
    title: "اتصل بنا",
    body: [
      "للاستفسارات التحريرية أو الإعلانية أو الفنية، يمكنك التواصل مع فريقنا عبر البريد: info@kassem.news.",
      "نرحّب بملاحظات القرّاء ومعلومات التصحيح. يُرجى إرسال الروابط والمعلومات الداعمة إلى: corrections@kassem.news.",
    ],
  },
  "editorial-policy": {
    title: "السياسة التحريرية",
    body: [
      "تُستورد الأخبار آلياً من خلاصات RSS ومصادر معلنة. لا يُعاد نشر النصوص الكاملة المحمية بحقوق الملكية، بل تُنشر ملخصات تحريرية بصياغة المنصة.",
      "تُحوَّل الأخبار الحساسة (الضحايا، العمليات العسكرية، الادعاءات، حالات الطوارئ، التقارير المتعارضة) إلى قائمة مراجعة بشرية قبل النشر.",
      "لا نصف أي خبر بأنه «مؤكد» إلا بعد التحقق الفعلي. وإذا تعذّر التحقق، يُوسم الخبر بأنه «قيد التطور» أو «غير مؤكد».",
    ],
  },
  sources: {
    title: "منهجية المصادر",
    body: [
      "يعتمد النظام على سِجل مصادر قابل للتحكم يُدار من لوحة التحكم دون تعديل الشيفرة، ويدعم خلاصات RSS وواجهات API.",
      "تُصنّف المصادر بحسب مستوى الثقة، وتُخضع المصادر ذات الأجندة الواضحة أو المجمّعات الإخبارية للمراجعة الإلزامية.",
      "لا يتم تفعيل أي مصدر قبل التحقق من توفّر الخلاصة والالتزام بشروط الاستخدام وحقوق النشر.",
    ],
  },
  corrections: {
    title: "التصحيحات",
    body: [
      "نحتفظ بسجل كامل للتصحيحات والتعديلات على كل خبر، مع السبب وموظف التحرير المسؤول.",
      "عند اكتشاف خطأ، تُحدَّث المادة ويُوثَّق التصحيح ظاهراً للجمهور وفق سياسة الشفافية.",
      "للإبلاغ عن خطأ في أي خبر: corrections@kassem.news.",
    ],
  },
  privacy: {
    title: "سياسة الخصوصية",
    body: [
      "نجمع الحد الأدنى من البيانات اللازمة لتشغيل الخدمة، مثل بريد المشتركين في النشرة الإخبارية وسجلات الاستخدام الأساسية.",
      "لا نبيع البيانات الشخصية لأي طرف ثالث، ونستخدمها فقط لأغراض تحسين الخدمة والتواصل الاختياري.",
      "يمكن للمستخدم طلب حذف بياناته عبر التواصل على privacy@kassem.news.",
    ],
  },
};

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const page = PAGES[slug];
  return { title: page?.title ?? "صفحة", alternates: { canonical: `/page/${slug}` } };
}

export default async function StaticPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const page = PAGES[slug];
  if (!page) notFound();
  const others = Object.entries(PAGES).filter(([key]) => key !== slug);

  return (
    <div>
      <PageHero kicker="عن المنصة" title={page.title} />
      <div className="grid gap-8 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <div className="article-body max-w-3xl">
            {page.body.map((p, i) => (
              <p key={i} className="flex gap-4">
                <span className="mt-1 font-display text-sm font-bold text-brand">{String(i + 1).padStart(2, "0")}</span>
                <span>{p}</span>
              </p>
            ))}
          </div>
        </div>
        <aside className="lg:col-span-4">
          <section className="paper-panel p-5 lg:sticky lg:top-44">
            <p className="kicker mb-3">صفحات ذات صلة</p>
            <ul className="divide-y divide-edge">
              {others.map(([key, item]) => (
                <li key={key}>
                  <Link href={`/page/${key}`} className="flex items-center justify-between gap-2 py-2.5 text-sm font-bold hover:text-brand-bright">
                    {item.title}
                    <span aria-hidden>←</span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        </aside>
      </div>
    </div>
  );
}
