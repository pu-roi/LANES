import { Button } from "@/shared/ui";

export function ActiveFloodMapStatus({ error, loading, refreshing, empty, hasFeatures, onRetry }: {
  error: string | null; loading: boolean; refreshing: boolean; empty: boolean;
  hasFeatures: boolean; onRetry: () => void;
}) {
  if (error) return <div role="alert" className="flex flex-wrap items-center gap-2 px-3 py-2 text-xs text-red-800">
    <p className="min-w-0 flex-1">{error}{hasFeatures ? " Previously loaded floods remain visible and may be out of date." : ""}</p>
    <Button variant="outline" size="sm" className="min-h-11 md:min-h-0" onClick={onRetry}>Retry flood map</Button>
  </div>;
  if (loading || refreshing) return <p role="status" className="px-3 py-2 text-xs text-slate-600">
    {hasFeatures ? "Updating flood map…" : "Loading active flood map…"}
  </p>;
  if (empty) return <p role="status" className="px-3 py-2 text-xs text-slate-600">No active floods have mapped boundaries.</p>;
  return null;
}
