import { Card, CardContent, Skeleton } from "@/shared/ui";

export default function NewsIntelligenceLoading() {
  return (
    <div role="status" aria-label="Loading News Intelligence" className="mx-auto w-full max-w-[1600px] space-y-6">
      <span className="sr-only">Loading News Intelligence…</span>
      <Skeleton className="h-8 w-48" /><Skeleton className="h-4 w-full max-w-lg" /><Skeleton className="h-12 w-full" />
      <Card className="shadow-sm"><CardContent className="space-y-3 p-6">
        <Skeleton className="h-6 w-40" /><Skeleton className="h-4 w-full max-w-xl" />
      </CardContent></Card>
    </div>
  );
}
