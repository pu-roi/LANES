import { Calendar, Clock, Droplets, MapPin, Ruler } from "lucide-react";
import type { ReactNode } from "react";
import { FloodDetailMetric } from "./FloodDetailMetric";

/** Labels and facts are supplied by the backend; timestamps are formatted by callers. */
export interface FloodLocationSummaryData {
  location: string;
  area?: string | null;
  locationQualifier?: string | null;
  waterLevel: string;
  condition: string;
  floodTimeLabel: string;
  floodTime: string;
  publishedAt?: string;
  mapStatus: string;
}

export function FloodLocationSummary({ data, compact = false, showPublication = true, locationDetails }: { data: FloodLocationSummaryData; compact?: boolean; showPublication?: boolean; locationDetails?: ReactNode }) {
  return <div className="space-y-4">
    <div className="flex items-start gap-3"><MapPin className="mt-0.5 size-5 shrink-0 text-blue-600" aria-hidden="true" /><div className="min-w-0"><h3 className="break-words text-base font-bold text-slate-900">{data.location}</h3>{data.area && <p className="mt-1 break-words text-sm text-slate-500">{data.area}</p>}{data.locationQualifier && <p className="mt-1 break-words text-sm text-slate-600">{data.locationQualifier}</p>}</div></div>
    {locationDetails}
    <div className="grid gap-3 sm:grid-cols-2">
      <FloodDetailMetric icon={<Ruler className="size-4" />} iconClassName="bg-blue-100 text-blue-600" label="Water level" value={data.waterLevel} />
      <FloodDetailMetric icon={<Clock className="size-4" />} iconClassName="bg-violet-100 text-violet-600" label={data.floodTimeLabel} value={data.floodTime} />
      {!compact && <><div className={showPublication ? "" : "sm:col-span-2"}><FloodDetailMetric icon={<Droplets className="size-4" />} iconClassName="bg-cyan-100 text-cyan-600" label="Condition in article" value={data.condition} /></div>{showPublication && <FloodDetailMetric icon={<Calendar className="size-4" />} iconClassName="bg-emerald-100 text-emerald-600" label="Article published" value={data.publishedAt ?? "Publication time unavailable"} />}</>}
    </div>
    {!compact && <p className="text-xs text-amber-800">{data.mapStatus}</p>}
  </div>;
}
