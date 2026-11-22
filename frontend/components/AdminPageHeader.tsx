import type { ReactNode } from "react";

export default function AdminPageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4 border-b border-edge pb-4">
      <div>
        <p className="kicker">لوحة التحكم</p>
        <h1 className="mt-1 font-display text-3xl font-extrabold tracking-tight text-ink">{title}</h1>
        {description && <p className="mt-2 max-w-3xl text-sm leading-relaxed text-ink-muted">{description}</p>}
      </div>
      {actions}
    </div>
  );
}
