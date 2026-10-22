import { Search, SlidersHorizontal } from "lucide-react";
import { Input, Select } from "@/shared/ui";
import { SpatialPanelButton as Button } from "./FloodRecordSummary";

function locationOptions(label: string, values: string[] = [], selected = "") {
  const displayed = selected && !values.includes(selected) ? [selected, ...values] : values;
  return [{ value: "", label }, ...displayed.map((value) => ({ value, label: value }))];
}

export function SpatialQueueFilters({ id, searchLabel, search, onSearch, city, onCity, barangay, onBarangay,
  severity, onSeverity, expanded, onExpanded, facets, onClear }: {
  id: string; searchLabel: string; search: string; onSearch: (value: string) => void;
  city: string; onCity: (value: string) => void; barangay: string; onBarangay: (value: string) => void;
  severity: string; onSeverity: (value: string) => void; expanded: boolean; onExpanded: (value: boolean) => void;
  facets?: { cities: string[]; barangays: string[] }; onClear: () => void;
}) {
  return <div className="space-y-2 border-b border-slate-100 p-3">
    <div className="flex items-center gap-2"><Input type="search" aria-label={searchLabel} placeholder="Search location, report or evidence" maxLength={120} value={search} onChange={(event) => onSearch(event.target.value)} leftIcon={<Search className="size-4" />} className="text-xs shadow-none" />
      <Button variant="outline" aria-expanded={expanded} aria-controls={id} onClick={() => onExpanded(!expanded)} className="gap-1.5 px-2"><SlidersHorizontal className="size-3.5" />Filters</Button></div>
    {expanded && <div id={id} className="grid grid-cols-2 gap-2">
      <Select className="[&_button>span]:truncate [&_button>span]:min-w-0 max-md:[&_button]:min-h-11" ariaLabel="Filter by city" label="City" value={city} options={locationOptions("All cities", facets?.cities, city)} onChange={(event) => onCity(String(event.target.value))} />
      <Select className="[&_button>span]:truncate [&_button>span]:min-w-0 max-md:[&_button]:min-h-11" ariaLabel="Filter by barangay" label="Barangay" disabled={!city} value={barangay} options={city ? locationOptions("All barangays", facets?.barangays, barangay) : [{ value: "", label: "Select a city first" }]} onChange={(event) => onBarangay(String(event.target.value))} />
      <Select className="[&_button>span]:truncate [&_button>span]:min-w-0 max-md:[&_button]:min-h-11" ariaLabel="Filter by severity" label="Severity" value={severity} options={[{ value: "", label: "All severities" }, { value: "low", label: "Low" }, { value: "medium", label: "Medium" }, { value: "high", label: "High" }, { value: "extreme", label: "Extreme" }, { value: "unknown", label: "Unassessed" }]} onChange={(event) => onSeverity(String(event.target.value))} />
    </div>}
    {!!(search || city || barangay || severity) && <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500"><span>{[city, barangay, severity].filter(Boolean).join(" · ") || "Search applied"}</span><Button variant="ghost" onClick={onClear}>Clear filters</Button></div>}
  </div>;
}
