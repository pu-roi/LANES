import { Layers, Newspaper, UserRound } from "lucide-react";
import { Button } from "@/shared/ui";
import { FloodSeverityBadge, FloodDepthBadge } from "../components/FloodRecordSummary";
import { parseUtcDate } from "@/lib/utils";
import type { ReviewItem } from "./reviewApi";

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
  const measurements = <span className="flex flex-wrap gap-1.5">
    {item.severity_levels?.length ? item.severity_levels.map((severity) => <FloodSeverityBadge key={severity} severity={severity} />) : <FloodSeverityBadge severity={grouped ? null : item.severity} />}
    {!grouped && item.depth && <FloodDepthBadge depth={item.depth} />}
    {grouped && item.depth_levels?.slice(0, 3).map((depth) => <FloodDepthBadge key={depth} depth={depth} />)}
    {grouped && (item.depth_levels?.length ?? 0) > 3 && <span className="text-[10px] text-slate-500">More depths in details</span>}
  </span>;
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
      <span className="min-w-0 break-words text-sm font-semibold text-slate-900">{item.location_summary || item.location}</span>
      {item.area_summary && <span className="break-words text-xs text-slate-500">{item.area_summary}</span>}
      {measurements}
      {!grouped && <><span className="break-words text-xs text-slate-500">{item.title}</span><span className="line-clamp-2 break-words text-sm leading-5 text-slate-700">{item.evidence}</span><span className="break-words text-xs text-amber-800">{item.review_reason}</span></>}
      {grouped && <><span className="line-clamp-2 break-words text-xs leading-5 text-slate-700">{item.evidence}</span><span className="text-[10px] text-slate-500">Latest report: {stamp?.toLocaleString("en-PH", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }) ?? "Time unavailable"}</span><span className="break-words text-xs leading-5 text-slate-600">Related evidence · Review each report before merging.</span></>}
    </Button>
  </article>;
}
