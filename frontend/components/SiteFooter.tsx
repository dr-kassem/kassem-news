import Link from "next/link";
import Logo from "./Logo";

const COLUMNS = [
  {
    title: "عن المنصة",
    links: [
      { href: "/page/about", label: "من نحن" },
      { href: "/page/editorial-policy", label: "السياسة التحريرية" },
      { href: "/page/sources", label: "منهجية المصادر" },
      { href: "/page/corrections", label: "التصحيحات" },
    ],
  },
  {
    title: "الأقسام",
    links: [
      { href: "/region/lebanon", label: "لبنان" },
      { href: "/region/middle-east", label: "الشرق الأوسط" },
      { href: "/section/world", label: "العالم" },
      { href: "/section/economy", label: "اقتصاد" },
    ],
  },
  {
    title: "عام",
    links: [
      { href: "/page/contact", label: "اتصل بنا" },
      { href: "/page/privacy", label: "سياسة الخصوصية" },
      { href: "/on-this-day", label: "في مثل هذا اليوم" },
    ],
  },
];

export default function SiteFooter() {
  return (
    <footer className="mt-16 border-t border-edge bg-surface/60">
      <div className="border-b-4 border-brand" aria-hidden />
      <div className="container-page grid gap-8 py-10 md:grid-cols-4">
        <div className="md:border-l md:border-edge md:pl-6">
          <Logo />
          <p className="mt-4 max-w-xs text-sm leading-relaxed text-ink-muted">
            قاسم نيوز — العالم في الصورة الكاملة. تغطية إخبارية عالمية مع تركيز خاص على لبنان والشرق الأوسط.
          </p>
        </div>
        {COLUMNS.map((col) => (
          <div key={col.title} className="md:border-l md:border-edge md:pl-6">
            <p className="kicker mb-3">{col.title}</p>
            <ul className="space-y-2 text-sm">
              {col.links.map((l) => (
                <li key={l.href}>
                  <Link href={l.href} className="link-muted">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t border-edge">
        <div className="container-page flex flex-col gap-2 py-4 text-xs text-ink-muted sm:flex-row sm:items-center sm:justify-between">
          <span>يخضع المحتوى لسياسة النشر والتصحيحات.</span>
          <span>Kassem News — العالم في الصورة الكاملة</span>
        </div>
      </div>
    </footer>
  );
}
