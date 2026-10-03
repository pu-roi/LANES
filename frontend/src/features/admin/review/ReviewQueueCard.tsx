import { Layers, Newspaper, UserRound } from "lucide-react";
import { Button } from "@/shared/ui";
import { formatFloodDepth } from "@/lib/floodDepth";
import { parseUtcDate } from "@/lib/utils";
import type { ReviewItem } from "./reviewApi";

const severityColors: Record<string, string> = {
  low: "bg-lime-100 text-lime-900", medium: "bg-amber-100 text-amber-900",
  high: "bg-orange-100 text-orange-900", extreme: "bg-red-100 text-red-900",
};

export function ReviewQueueCard({ item, onInspect }: {
  item: ReviewItem; onInspect: (key: string, opener: HTMLButtonElement) => void;
}) {
  const news = item.source === "news_claim";
  const count = item.member_count ?? 1;
  const grouped = count > 1;
  const Icon = news ? Newspaper : UserRound;
  const sourceLabel = news ? "News claim" : "User report";
  const stamp = parseUtcDate(item.queued_at);
  const inspectLabel = (row: ReviewItem) => `Inspect ${row.source === "news_claim" ? "news claim" : "user report"}: ${row.location}`;
  const measurements = (row: ReviewItem) => <div className="flex flex-wrap gap-1.5">
    {row.severity && <span className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${severityColors[row.severity.toLowerCase()] ?? "bg-slate-100 text-slate-700"}`}>{row.severity}</span>}
    {row.depth && <span className="rounded bg-sky-100 px-2 py-0.5 text-[10px] font-medium text-sky-900">{formatFloodDepth(row.depth, { compact: true })}</span>}
  </div>;
  return <article aria-label={`${sourceLabel}: ${item.location}${grouped ? ` · ${count} related reports` : ""}`}
    className={`overflow-hidden rounded-xl border-l-4 ${news ? "border-violet-400 bg-violet-50/70" : "border-sky-400 bg-sky-50/70"}`}>
    <Button variant="ghost" className={`h-auto min-h-11 w-full flex-col items-stretch gap-2 rounded-none p-4 text-left font-normal focus:ring-inset focus:ring-offset-0 ${news ? "hover:bg-violet-100/70 focus:ring-violet-500" : "hover:bg-sky-100/70 focus:ring-sky-500"}`}
      aria-label={inspectLabel(item)}
      onClick={(event) => onInspect(item.key, event.currentTarget)}>
      <span className="flex flex-wrap items-center justify-between gap-2">
        <span className={`inline-flex items-center gap-1.5 text-xs font-semibold ${news ? "text-violet-800" : "text-sky-800"}`}><Icon className="size-3.5 shrink-0" />{grouped ? "User reports" : sourceLabel}</span>
        {grouped ? <span className="inline-flex items-center gap-1 rounded-full bg-sky-100 px-2 py-1 text-[11px] font-semibold text-sky-900"><Layers className="size-3" />{count} related</span>
          : stamp && <time dateTime={item.queued_at} className="text-[10px] text-slate-500">{stamp.toLocaleString("en-PH", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}</time>}
      </span>
      <span className="min-w-0 break-words text-sm font-semibold text-slate-900">{item.location}</span>
      {!grouped && <>{measurements(item)}<span className="break-words text-xs text-slate-500">{item.title}</span><span className="line-clamp-2 break-words text-sm leading-5 text-slate-700">{item.evidence}</span><span className="break-words text-xs text-amber-800">{item.review_reason}</span></>}
      {grouped && <span className="break-words text-xs leading-5 text-slate-600">Nearby reports on the same road. Open to review their evidence.</span>}
    </Button>
  </article>;
}
