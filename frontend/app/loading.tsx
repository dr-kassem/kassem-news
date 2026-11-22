export default function Loading() {
  return (
    <div className="container-page py-10" aria-busy="true" aria-live="polite">
      <div className="mb-8 border-b border-edge pb-4">
        <div className="h-3 w-24 animate-pulse bg-surface" />
        <div className="mt-3 h-10 w-2/3 animate-pulse bg-surface" />
      </div>
      <div className="grid gap-6 lg:grid-cols-12">
        <div className="space-y-4 lg:col-span-8">
          <div className="h-72 animate-pulse border border-edge bg-surface/60" />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-56 animate-pulse border border-edge bg-surface/60" />
            ))}
          </div>
        </div>
        <div className="space-y-4 lg:col-span-4">
          <div className="h-80 animate-pulse border border-edge bg-surface/60" />
        </div>
      </div>
    </div>
  );
}
