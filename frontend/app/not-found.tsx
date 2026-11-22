import Link from "next/link";

export default function NotFound() {
  return (
    <html lang="ar" dir="rtl">
      <body className="flex min-h-screen items-center justify-center bg-base p-6 font-sans text-ink">
        <div className="w-full max-w-lg border-y-4 border-brand bg-surface/50 px-8 py-12 text-center">
          <p className="font-display text-7xl font-extrabold text-brand/40">404</p>
          <h1 className="mt-4 font-display text-3xl font-extrabold">الصفحة غير موجودة</h1>
          <p className="mt-3 text-sm leading-relaxed text-ink-muted">
            الرابط الذي طلبته غير متاح أو تم نقل الصفحة.
          </p>
          <Link href="/" className="btn-primary mt-6 inline-flex">
            العودة إلى الرئيسية
          </Link>
        </div>
      </body>
    </html>
  );
}
