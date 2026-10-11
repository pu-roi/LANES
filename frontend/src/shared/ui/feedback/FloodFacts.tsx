import { Car, EyeOff, Map, Ruler } from "lucide-react";
import { FloodDetailMetric } from "./FloodDetailMetric";
import { formatFloodDepth } from "@/lib/floodDepth";
import { formatHazards, formatPassableVehicles } from "@/lib/floodSurvey";

export function FloodSeverityBadge({ severity }: { severity?: string | null }) {
  const labels: Record<string, string> = { low: "Passable (Low)", medium: "Warning (Medium)", high: "Hazardous (High)", extreme: "Impassable (Extreme)" };
  const colors: Record<string, string> = { low: "border-lime-200 bg-lime-100 text-lime-800", medium: "border-yellow-200 bg-yellow-100 text-yellow-800", high: "border-orange-200 bg-orange-100 text-orange-800", extreme: "border-red-200 bg-red-100 text-red-800" };
  return <span className={`rounded-full border px-2.5 py-1 text-xs font-bold uppercase ${colors[severity ?? ""] ?? "bg-slate-100 text-slate-600"}`}>{labels[severity ?? ""] ?? "Not recorded"}</span>;
}

export function FloodFacts({ depth, hazards, vehicles, bidirectional }: { depth?: string | null; hazards?: string | null; vehicles?: string | string[] | null; bidirectional?: boolean | null }) {
  return <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2">
    <FloodDetailMetric icon={<Ruler className="size-4" />} iconClassName="bg-blue-100 text-blue-600" label="Water Level" value={formatFloodDepth(depth, { fallback: "Not recorded" })} />
    <FloodDetailMetric icon={<EyeOff className="size-4" />} iconClassName="bg-amber-100 text-amber-600" label="Submerged Hazards" value={formatHazards(hazards)} />
    <FloodDetailMetric icon={<Map className="size-4" />} iconClassName="bg-violet-100 text-violet-600" label="Road Coverage" value={bidirectional == null ? "Not recorded" : bidirectional ? "Both directions" : "One direction"} />
    <FloodDetailMetric icon={<Car className="size-4" />} iconClassName="bg-emerald-100 text-emerald-600" label="Passable Vehicles" value={formatPassableVehicles(vehicles)} />
  </div>;
}
