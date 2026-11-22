"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import Logo from "./Logo";
import SearchBox from "./SearchBox";
import ThemeToggle from "./ThemeToggle";

const NAV = [
  { href: "/", label: "الرئيسية" },
  { href: "/breaking", label: "عاجل" },
  { href: "/strikes", label: "الغارات" },
  { href: "/region/lebanon", label: "لبنان" },
  { href: "/region/middle-east", label: "الشرق الأوسط" },
  { href: "/section/world", label: "العالم" },
  { href: "/section/politics", label: "سياسة" },
  { href: "/section/economy", label: "اقتصاد" },
  { href: "/section/technology", label: "تكنولوجيا" },
  { href: "/section/cybersecurity", label: "أمن سيبراني" },
  { href: "/section/analysis", label: "تحليل وتحقيقات" },
  { href: "/kairos", label: "تحليلات كاييروس" },
  { href: "/on-this-day", label: "في مثل هذا اليوم" },
];

export default function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-edge bg-base/95 backdrop-blur-lg">
      <div className="container-page grid grid-cols-[1fr_auto] items-center gap-3 py-3 lg:grid-cols-[1fr_auto_1fr]">
        <div className="hidden lg:block">
          <p className="kicker">منصة إخبارية عربية</p>
          <p className="mt-0.5 text-xs text-ink-muted">العالم في الصورة الكاملة</p>
        </div>

        <div className="flex justify-start lg:justify-center">
          <Logo />
        </div>

        <div className="flex items-center justify-end gap-2">
          <div className="hidden w-full max-w-[230px] sm:block">
            <SearchBox />
          </div>
          <ThemeToggle />
          <button
            className="rounded-md border border-edge px-3 py-2 text-sm font-bold text-ink-muted lg:hidden"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-controls="main-nav"
            aria-label="القائمة"
          >
            {open ? "✕" : "☰"}
          </button>
        </div>
      </div>

      <div className="container-page pb-3 sm:hidden">
        <SearchBox />
      </div>

      <nav id="main-nav" aria-label="التنقل الرئيسي" className="border-t border-edge bg-surface/60">
        <div className="container-page flex items-center gap-4">
          <span className="hidden shrink-0 text-[10px] font-bold uppercase tracking-[0.22em] text-ink-muted md:block">
            الأقسام
          </span>
          <ul
            className={`${
              open ? "flex" : "hidden"
            } flex-1 flex-wrap items-center gap-1 py-2 lg:flex lg:py-1.5`}
          >
            {NAV.map((item) => {
              const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={() => setOpen(false)}
                    className={`inline-flex rounded-full px-3 py-1.5 text-[13px] font-bold transition-colors ${
                      active ? "bg-brand text-brand-fg" : "text-ink-muted hover:bg-card hover:text-ink"
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      </nav>
    </header>
  );
}
