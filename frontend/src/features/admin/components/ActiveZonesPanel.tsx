import React, { useState } from "react";
import { Loader2, CheckCircle, Shield, Pencil } from "lucide-react";
import { ZoneContributors } from "./ZoneContributors";
import { FloodRecordSummary, SpatialPanelButton as Button, floodRecordTime } from "./FloodRecordSummary";
import { Pagination } from "@/shared/ui";
import type { AvoidanceZone } from "@/features/admin/adminApi";

interface ActiveZonesPanelProps {
  activeOnly: boolean;
  setActiveOnly: (active: boolean) => void;
  page: number;
  setPage: (page: number) => void;
  selectedIds: number[];
  setSelectedIds: (ids: number[]) => void;
  selectedZoneId: number | null;
  setSelectedZoneId: (id: number | null) => void;
  selectedContributorId?: number | null;
  setSelectedContributorId?: (id: number | null) => void;
  zones: AvoidanceZone[];
  listLoading: boolean;
  isPlaceholderData: boolean;
  totalPages: number;
  flyToZone: (zone: AvoidanceZone) => void;
  setConfirmId: (id: number | null) => void;
  onCreateOfficialZone?: () => void;
  onEditZone?: (zone: AvoidanceZone) => void;
}

export function ActiveZonesPanel({
  activeOnly,
  setActiveOnly,
  page,
  setPage,
  selectedIds,
  setSelectedIds,
  selectedZoneId,
  setSelectedZoneId,
  selectedContributorId,
  setSelectedContributorId,
  zones,
  listLoading,
  isPlaceholderData,
  totalPages,
  flyToZone,
  setConfirmId,
  onCreateOfficialZone,
  onEditZone,
}: ActiveZonesPanelProps) {
  const [expandedZoneIds, setExpandedZoneIds] = useState<number[]>([]);

  const toggleExpand = (zoneId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setExpandedZoneIds((prev) =>
      prev.includes(zoneId) ? prev.filter((id) => id !== zoneId) : [...prev, zoneId]
    );
  };

  const handleContributorClick = (reportId: number, zone: AvoidanceZone, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!setSelectedContributorId) return;

    if (selectedContributorId === reportId) {
      // Deselect contributor and restore parent zone view
      setSelectedContributorId(null);
      setSelectedZoneId(zone.id);
    } else {
      // Focus on this specific contributor's report geometry
      setSelectedContributorId(reportId);
      setSelectedZoneId(zone.id);
    }
  };

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedIds(zones.filter(z => z.is_active).map(z => z.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectRow = (id: number, checked: boolean) => {
    if (checked) {
      setSelectedIds([...selectedIds, id]);
    } else {
      setSelectedIds(selectedIds.filter((selectedId) => selectedId !== id));
    }
  };

  return (
    <section aria-label="Active Zones" className="flex min-h-0 flex-1 flex-col overflow-hidden">
      {/* Filter Toolbar */}
      <div className="p-3 border-b border-gray-100 flex flex-wrap items-center justify-between bg-white gap-2">
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="selectAll"
            checked={selectedIds.length > 0 && selectedIds.length === zones.filter((z: AvoidanceZone) => z.is_active).length}
            onChange={handleSelectAll}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 w-4 h-4 cursor-pointer"
          />
          <label htmlFor="selectAll" className="text-xs font-semibold text-gray-700 cursor-pointer">
            Select All Active
          </label>
        </div>

        {onCreateOfficialZone && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onCreateOfficialZone}
            className="md:hidden px-2.5 gap-1 border-blue-200 text-blue-700 hover:bg-blue-50"
          >
            <Shield className="h-3.5 w-3.5" />
            Create
          </Button>
        )}

        <div className="flex items-center gap-1 bg-gray-100 p-0.5 rounded-lg text-xs ml-auto">
          <Button variant="ghost"
            onClick={() => { setActiveOnly(true); setPage(1); }}
            aria-pressed={activeOnly}
            className={`px-2 ${activeOnly ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
          >
            Active Only
          </Button>
          <Button variant="ghost"
            onClick={() => { setActiveOnly(false); setPage(1); }}
            aria-pressed={!activeOnly}
            className={`px-2 ${!activeOnly ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
          >
            All History
          </Button>
        </div>
      </div>

      {/* Zones List Content */}
      <div className="scrollbar-auto-hide flex-1 overflow-y-auto divide-y divide-gray-100 pb-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom))] md:pb-3">
        {listLoading && !isPlaceholderData ? (
          <div className="flex flex-col items-center justify-center h-48 text-gray-400 gap-2">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
            <span className="text-xs font-medium">Loading zones...</span>
          </div>
        ) : zones.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-gray-400 gap-2 p-6 text-center">
            <CheckCircle className="w-8 h-8 text-emerald-500/50" />
            <span className="text-sm font-semibold text-gray-700">No Detour Zones Found</span>
            <p className="text-xs text-gray-400">No zones match this view. Unreported flood hazards may still be present.</p>
          </div>
        ) : (
          zones.map((zone: AvoidanceZone) => {
            const isSelected = selectedZoneId === zone.id;
            const isExpanded = expandedZoneIds.includes(zone.id);

            return (
              <div
                key={zone.id}
                role="article"
                aria-label={`Zone #${zone.id}`}
                onClick={() => {
                  if (isSelected) {
                    setSelectedZoneId(null);
                    if (setSelectedContributorId) setSelectedContributorId(null);
                  } else {
                    setSelectedZoneId(zone.id);
                    if (setSelectedContributorId) setSelectedContributorId(null);
                    flyToZone(zone);
                  }
                }}
                className={`p-4 transition-colors cursor-pointer hover:bg-blue-50/80 ${
                  isSelected ? "bg-blue-50/80" : selectedIds.includes(zone.id) ? "bg-blue-50/40" : ""
                }`}
              >
                <FloodRecordSummary title={`Zone #${zone.id}`} severity={zone.severity} depth={zone.depth}
                  timestamp={zone.created_at} text={zone.report_text} location={zone.name}
                  headingExtra={<>
                    {zone.is_active && <input type="checkbox" aria-label={`Select Zone #${zone.id}`} checked={selectedIds.includes(zone.id)} onChange={(event) => handleSelectRow(zone.id, event.target.checked)} onClick={(event) => event.stopPropagation()} className="size-4 rounded border-gray-300 text-blue-600" />}
                    <span className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${zone.is_active ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-500"}`}>{zone.is_active ? "Active" : "Inactive"}</span>
                  </>}
                  facts={[
                    { label: "Source", value: zone.report_source === "direct_user" ? "User report" : zone.report_source?.replaceAll("_", " ") || "Official zone" },
                    ...(zone.report_id ? [{ label: "Primary report", value: `Report #${zone.report_id}` }] : []),
                    { label: "Expires", value: zone.expires_at ? floodRecordTime(zone.expires_at) : "No expiry recorded" },
                    { label: "Vehicles", value: zone.passable_vehicles || "Not recorded" },
                    { label: "Hazards", value: zone.hidden_hazards || "Not recorded" },
                    ...(zone.admin_notes ? [{ label: "Admin notes", value: zone.admin_notes }] : []),
                  ]}
                  actions={<>
                    <Button variant="outline" onClick={() => { setSelectedZoneId(zone.id); setSelectedContributorId?.(null); flyToZone(zone); }}>View on map</Button>
                  {onEditZone && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => onEditZone(zone)}
                      className="text-xs px-2.5 border-slate-200 text-slate-700 hover:bg-slate-50 gap-1 rounded-lg"
                      title="Edit zone attributes & overrides"
                    >
                      <Pencil className="w-3 h-3 text-slate-500" />
                      Edit
                    </Button>
                  )}
                  {zone.is_active && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setConfirmId(zone.id)}
                      className="text-xs px-3 border-red-200 text-red-600 hover:bg-red-50 rounded-lg"
                    >
                      Deactivate
                    </Button>
                  )}
                  </>}
                >
                  <ZoneContributors zone={zone} expanded={isExpanded} selectedId={selectedContributorId} onToggle={(event) => toggleExpand(zone.id, event)} onInspect={(id, event) => handleContributorClick(id, zone, event)} />
                </FloodRecordSummary>
              </div>
            );
          })
        )}
      </div>

      {/* Pagination */}
      <div className="p-3 border-t border-gray-200 bg-white">
        <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
      </div>
    </section>
  );
}
