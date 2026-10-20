import type { ReactNode } from "react";
import { Layers, type LucideIcon } from "lucide-react";
import { Button } from "@/shared/ui";
import { FloodSeverityBadge, FloodDepthBadge } from "./FloodRecordSummary";
import { parseUtcDate } from "@/lib/utils";

const tones = {
  user: { card: "border-sky-400 bg-sky-50/70", button: "hover:bg-sky-100/70 focus:ring-sky-500", text: "text-sky-800" },
  news: { card: "border-violet-400 bg-violet-50/70", button: "hover:bg-violet-100/70 focus:ring-violet-500", text: "text-violet-800" },
  zone: { card: "border-emerald-400 bg-emerald-50/70", button: "hover:bg-emerald-100/70 focus:ring-emerald-500", text: "text-emerald-800" },
};

/** Presentation only: membership, summaries and eligibility come from the backend. */
export function SpatialGroupCard({ label, inspectLabel, sourceLabel, location, area, count, countLabel = "related",
  timestamp, tone, icon: Icon, severities = [], depths = [], onInspect, children }: {
  label: string; inspectLabel: string; sourceLabel: string; location: string; area?: string;
  count: number; countLabel?: string; timestamp: string; tone: keyof typeof tones; icon: LucideIcon;
  severities?: (string | null | undefined)[]; depths?: string[];
  onInspect: (button: HTMLButtonElement) => void; children: ReactNode;
}) {
  const style = tones[tone];
  const stamp = parseUtcDate(timestamp);
  return <article aria-label={label} className={`overflow-hidden rounded-xl border-l-4 ${style.card}`}>
    <Button variant="ghost" aria-label={inspectLabel} onClick={(event) => onInspect(event.currentTarget)}
      className={`h-auto min-h-11 w-full flex-col items-stretch gap-2 rounded-none p-4 text-left font-normal focus:ring-inset focus:ring-offset-0 ${style.button}`}>
      <span className="flex flex-wrap items-center justify-between gap-2">
        <span className={`inline-flex items-center gap-1.5 text-xs font-semibold ${style.text}`}><Icon className="size-3.5 shrink-0" />{sourceLabel}</span>
        {count > 1 ? <span className="inline-flex items-center gap-1 rounded-full bg-sky-100 px-2 py-1 text-[11px] font-semibold text-sky-900"><Layers className="size-3" />{count} {countLabel}</span>
          : stamp && <time dateTime={timestamp} className="text-[10px] text-slate-500">{stamp.toLocaleString("en-PH", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}</time>}
      </span>
      <span className="min-w-0 break-words text-sm font-semibold text-slate-900">{location}</span>
      {area && <span className="break-words text-xs text-slate-500">{area}</span>}
      <span className="flex flex-wrap gap-1.5">
        {(severities.length ? severities : [null]).map((severity, index) => <FloodSeverityBadge key={severity ?? index} severity={severity} />)}
        {depths.slice(0, 3).map((depth) => <FloodDepthBadge key={depth} depth={depth} />)}
        {depths.length > 3 && <span className="text-[10px] text-slate-500">More depths in details</span>}
      </span>
      {children}
    </Button>
  </article>;
}
