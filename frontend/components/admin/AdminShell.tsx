"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Logo from "@/components/Logo";
import ThemeToggle from "@/components/ThemeToggle";
import { clearToken, getToken } from "@/lib/api";

const NAV = [
  { href: "/admin", label: "نظرة عامة" },
  { href: "/admin/review", label: "قائمة المراجعة" },
  { href: "/admin/articles", label: "إدارة الأخبار" },
  { href: "/admin/duplicates", label: "الأخبار المكرّرة" },
  { href: "/admin/sources", label: "المصادر" },
  { href: "/admin/rules", label: "قواعد النشر" },
  { href: "/admin/runs", label: "التوريد والسجلات" },
  { href: "/admin/ai", label: "مساعد الذكاء" },
];

export default function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [checked, setChecked] = useState(false);
  const isLogin = pathname === "/admin/login";

  useEffect(() => {
    if (isLogin) {
      setChecked(true);
      return;
    }
    if (!getToken()) router.replace("/admin/login");
    else setChecked(true);
  }, [isLogin, pathname, router]);

  if (isLogin) return <>{children}</>;

  if (!checked) {
    return (
      <div className="container-page py-20 text-center text-ink-muted">جارٍ التحقق من الجلسة…</div>
    );
  }

  return (
    <div className="min-h-screen bg-base lg:grid lg:grid-cols-[250px_1fr]">
      <aside className="border-b border-edge bg-surface lg:min-h-screen lg:border-b-0 lg:border-l">
        <div className="border-t-4 border-brand px-5 py-5">
          <Logo compact />
        </div>
        <nav aria-label="تنقل لوحة التحكم" className="px-3 pb-4">
          <p className="kicker px-3 py-2">الإدارة</p>
          <ul className="flex gap-1 overflow-x-auto pb-1 lg:block lg:space-y-1 lg:overflow-visible">
            {NAV.map((item) => {
              const active = item.href === "/admin" ? pathname === "/admin" : pathname.startsWith(item.href);
              return (
                <li key={item.href} className="shrink-0">
                  <Link
                    href={item.href}
                    className={`block whitespace-nowrap px-3 py-2 text-sm font-bold transition-colors ${
                      active ? "bg-brand text-brand-fg" : "text-ink-muted hover:bg-card hover:text-ink"
                    }`}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </aside>

      <div className="min-w-0">
        <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-edge bg-base/95 px-5 py-3 backdrop-blur lg:px-8">
          <div className="flex items-center gap-3">
            <span className="badge border-brand/50 bg-brand/10 text-brand-bright">لوحة التحكم</span>
            <span className="hidden text-xs text-ink-muted sm:inline">إدارة المحتوى والتوريد</span>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/" className="link-muted hidden text-sm sm:inline">
              عرض الموقع ↗
            </Link>
            <ThemeToggle />
            <button
              onClick={() => {
                clearToken();
                router.replace("/admin/login");
              }}
              className="btn-ghost px-3 py-1.5 text-xs"
            >
              خروج
            </button>
          </div>
        </header>
        <main className="p-5 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
