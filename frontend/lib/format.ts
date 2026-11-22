const AR_DATE = new Intl.DateTimeFormat("ar", {
  weekday: "long",
  year: "numeric",
  month: "long",
  day: "numeric",
});

const AR_TIME = new Intl.DateTimeFormat("ar", {
  hour: "2-digit",
  minute: "2-digit",
});

function toUtcDate(value: string | Date): Date {
  if (value instanceof Date) return value;
  const hasOffset = /(?:Z|[+-]\d{2}:?\d{2})$/.test(value.trim());
  return new Date(hasOffset ? value : `${value}Z`);
}

export function fullDate(value: string | Date | null | undefined): string {
  if (!value) return "";
  const date = toUtcDate(value);
  return `${AR_DATE.format(date)} — ${AR_TIME.format(date)}`;
}

export function shortDate(value: string | Date | null | undefined): string {
  if (!value) return "";
  const date = toUtcDate(value);
  return AR_DATE.format(date);
}

export function timeAgo(value: string | Date | null | undefined): string {
  if (!value) return "";
  const date = toUtcDate(value);
  const diff = Math.max(0, Date.now() - date.getTime());
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "الآن";
  if (minutes < 60) return `منذ ${minutes} دقيقة`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `منذ ${hours} ساعة`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `منذ ${days} يوم`;
  return shortDate(date);
}

export const VERIFICATION_LABELS: Record<string, string> = {
  confirmed: "مؤكد من المنصة",
  attributed: "منقول عن مصدر",
  developing: "خبر متطور",
  unconfirmed: "غير مؤكد",
};

export const VERIFICATION_STYLES: Record<string, string> = {
  confirmed: "bg-green-900/40 text-green-300 border-green-800",
  attributed: "bg-surface text-ink-muted border-edge",
  developing: "bg-amber-900/40 text-amber-300 border-amber-800",
  unconfirmed: "bg-brand/20 text-brand-bright border-brand/40",
};
