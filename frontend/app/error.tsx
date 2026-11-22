"use client";

export default function GlobalError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="container-page py-16">
      <div className="border-y-4 border-brand bg-surface/50 px-6 py-12 text-center">
        <p className="kicker">خطأ غير متوقع</p>
        <h1 className="mt-3 font-display text-4xl font-extrabold text-ink">تعذّر تحميل المحتوى</h1>
        <p className="mx-auto mt-3 max-w-lg text-sm leading-relaxed text-ink-muted">
          حدثت مشكلة أثناء جلب هذه الصفحة. يمكنك إعادة المحاولة.
        </p>
        <button onClick={reset} className="btn-primary mt-6">
          إعادة المحاولة
        </button>
      </div>
    </div>
  );
}
