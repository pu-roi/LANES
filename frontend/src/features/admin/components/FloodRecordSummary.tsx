import type { ReactNode } from "react";
import { MapPin } from "lucide-react";
import { Button } from "@/shared/ui";
import type { ButtonProps } from "@/shared/ui/forms/Button";
import { formatFloodDepth } from "@/lib/floodDepth";
import { parseUtcDate } from "@/lib/utils";

const severityStyles: Record<string, string> = {
  low: "bg-lime-100 text-lime-800 border-lime-300",
  medium: "bg-amber-100 text-amber-800 border-amber-300",
  high: "bg-orange-100 text-orange-800 border-orange-300",
  extreme: "bg-red-100 text-red-800 border-red-300",
};

/** Shared admin sizing; retain large touch targets on phones and touch screens. */
export function SpatialPanelButton({ className = "", size = "sm", ...props }: ButtonProps) {
  return <Button {...props} size={size} className={`max-md:min-h-11 [@media(pointer:coarse)]:min-h-11 ${className}`} />;
}

export function FloodSeverityBadge({ severity }: { severity?: string | null }) {
  return <span className={`rounded border px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wide ${severityStyles[severity?.toLowerCase() ?? ""] ?? "border-slate-200 bg-slate-100 text-slate-600"}`}>{severity || "Unassessed"}</span>;
}

export function FloodDepthBadge({ depth }: { depth: string }) {
  return <span className="rounded bg-blue-100 px-2 py-0.5 text-[10px] font-medium text-blue-700">{formatFloodDepth(depth, { compact: true })}</span>;
}

export function floodRecordTime(value?: string | null) {
  return parseUtcDate(value)?.toLocaleString("en-PH", { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" }) ?? "Time unavailable";
}

/** Flat presentation shared by pending evidence and published zones; actions stay with callers. */
export function FloodRecordSummary({ title, severity, depth, timestamp, text, location, headingExtra, aside, facts = [], children, actions }: {
  title: string; severity?: string | null; depth?: string | null; timestamp: string;
  text?: string | null; location?: string | null; headingExtra?: ReactNode; aside?: ReactNode;
  facts?: { label: string; value: ReactNode }[]; children?: ReactNode; actions?: ReactNode;
}) {
  return <>
    <div className="mb-2 flex items-start justify-between gap-2">
      <div className="flex min-w-0 flex-wrap items-center gap-2">
        {headingExtra}<span className="text-sm font-bold text-gray-900">{title}</span>
        <FloodSeverityBadge severity={severity} />{depth && <FloodDepthBadge depth={depth} />}
      </div>
      {aside && <div className="shrink-0">{aside}</div>}
    </div>
    <time dateTime={timestamp} className="mb-2 block text-[11px] text-slate-500">{floodRecordTime(timestamp)}</time>
    {text && <p className="mb-2 whitespace-pre-line break-words text-xs font-medium leading-5 text-slate-700">&ldquo;{text}&rdquo;</p>}
    {location && <p className="mb-3 flex items-start gap-1.5 text-xs text-slate-500"><MapPin className="mt-0.5 size-3.5 shrink-0 text-slate-400" /><span className="min-w-0 break-words">{location}</span></p>}
    {!!facts.length && <dl className="mb-3 space-y-1 text-xs leading-5">{facts.map(({ label, value }) => <div key={label} className="flex gap-2"><dt className="w-24 shrink-0 text-slate-500">{label}</dt><dd className="min-w-0 break-words text-slate-700">{value}</dd></div>)}</dl>}
    {children}
    {actions && <div className="mt-3 flex flex-wrap items-center justify-end gap-2 border-t border-gray-100 pt-2" onClick={(event) => event.stopPropagation()}>{actions}</div>}
  </>;
}
