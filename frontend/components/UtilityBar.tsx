import { fullDate } from "@/lib/format";

export default function UtilityBar() {
  const now = new Date();
  return (
    <div className="bg-ink text-base">
      <div className="container-page flex items-center justify-between gap-4 py-1.5 text-[11px] font-semibold">
        <div className="flex items-center gap-3">
          <span className="hidden sm:inline">{fullDate(now)}</span>
          <span className="hidden h-3 w-px bg-base/30 sm:inline-block" aria-hidden />
          <span>النسخة العربية</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-brand-bright animate-pulse" aria-hidden />
          <span>بث مباشر</span>
          <span className="hidden opacity-60 sm:inline">— تحديث كل دقيقة</span>
        </div>
      </div>
    </div>
  );
}
