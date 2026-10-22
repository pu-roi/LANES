import { Newspaper, UserRound } from "lucide-react";
import { SpatialGroupCard } from "../components/SpatialGroupCard";
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
  return <SpatialGroupCard label={`${sourceLabel}: ${item.location}${grouped ? ` · ${count} related reports` : ""}`}
    inspectLabel={inspectLabel(item)} sourceLabel={grouped ? "User reports" : sourceLabel}
    location={item.location_summary || item.location} area={item.area_summary} count={count}
    timestamp={item.queued_at} tone={news ? "news" : "user"} icon={Icon}
    severities={item.severity_levels?.length ? item.severity_levels : [grouped ? null : item.severity]}
    depths={grouped ? item.depth_levels : item.depth ? [item.depth] : []}
    onInspect={(button) => onInspect(item.key, button)}>
      {!grouped && <><span className="break-words text-xs text-slate-500">{item.title}</span><span className="line-clamp-2 break-words text-sm leading-5 text-slate-700">{item.evidence}</span><span className="break-words text-xs text-amber-800">{item.review_reason}</span></>}
      {grouped && <><span className="line-clamp-2 break-words text-xs leading-5 text-slate-700">{item.evidence}</span><span className="text-[10px] text-slate-500">Latest report: {stamp?.toLocaleString("en-PH", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }) ?? "Time unavailable"}</span><span className="break-words text-xs leading-5 text-slate-600">Related evidence · Review each report before merging.</span></>}
  </SpatialGroupCard>;
}
