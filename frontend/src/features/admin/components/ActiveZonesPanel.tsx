import React, { useState } from "react";
import { Loader2, CheckCircle, Clock, UserCheck, ChevronDown, ChevronUp, Shield } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/shared/ui/Button";
import { Pagination } from "@/shared/ui/Pagination";
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
    <>
      {/* Filter Toolbar */}
      <div className="p-3 border-b border-gray-100 flex items-center justify-between bg-white gap-2">
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

        <div className="flex items-center gap-1 bg-gray-100 p-0.5 rounded-lg text-xs">
          <button
            onClick={() => { setActiveOnly(true); setPage(1); }}
            className={`px-3 py-1 rounded-md font-medium transition-all ${activeOnly ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
          >
            Active Only
          </button>
          <button
            onClick={() => { setActiveOnly(false); setPage(1); }}
            className={`px-3 py-1 rounded-md font-medium transition-all ${!activeOnly ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
          >
            All History
          </button>
        </div>
      </div>

      {/* Zones List Content */}
      <div className="flex-1 overflow-y-auto divide-y divide-gray-100">
        {listLoading && !isPlaceholderData ? (
          <div className="flex flex-col items-center justify-center h-48 text-gray-400 gap-2">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
            <span className="text-xs font-medium">Loading zones...</span>
          </div>
        ) : zones.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-gray-400 gap-2 p-6 text-center">
            <CheckCircle className="w-8 h-8 text-emerald-500/50" />
            <span className="text-sm font-semibold text-gray-700">No Detour Zones Found</span>
            <p className="text-xs text-gray-400">All roads in Pasig City are currently open and clear of reported flood hazards.</p>
          </div>
        ) : (
          zones.map((zone: AvoidanceZone) => {
            const isSelected = selectedZoneId === zone.id;
            const isExpanded = expandedZoneIds.includes(zone.id);
            const contributors = zone.contributors || [];
            const hasMultipleContributors = contributors.length > 1;

            return (
              <div
                key={zone.id}
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
                className={`p-4 transition-all cursor-pointer hover:bg-slate-50/80 ${
                  isSelected ? "bg-blue-50/80 ring-2 ring-blue-500/30" : selectedIds.includes(zone.id) ? "bg-blue-50/40" : ""
                }`}
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-3">
                    {zone.is_active && (
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(zone.id)}
                        onChange={(e) => handleSelectRow(zone.id, e.target.checked)}
                        onClick={(e) => e.stopPropagation()}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 w-4 h-4 cursor-pointer mt-0.5"
                      />
                    )}
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-gray-900">Zone #{zone.id}</span>
                        {zone.is_active ? (
                          <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-700 text-[10px] font-bold tracking-wide uppercase">Active</span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-500 text-[10px] font-bold tracking-wide uppercase">Inactive</span>
                        )}
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border ${
                          zone.severity?.toLowerCase() === "low"
                            ? "bg-lime-100 text-lime-800 border-lime-300"
                            : zone.severity?.toLowerCase() === "medium"
                            ? "bg-amber-100 text-amber-800 border-amber-300"
                            : zone.severity?.toLowerCase() === "high"
                            ? "bg-orange-100 text-orange-800 border-orange-300"
                            : "bg-red-100 text-red-800 border-red-300 animate-pulse"
                        }`}>
                          {zone.severity}
                        </span>
                      </div>
                      {zone.report_id && (
                        <p className="text-xs text-gray-500 mt-0.5 font-medium">Primary Report #{zone.report_id}</p>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-1.5 text-xs text-gray-600 pl-7 mb-3">
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-gray-400" />
                    Created: {new Date(zone.created_at).toLocaleDateString()} {new Date(zone.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </div>

                  {/* Reporter Tag with Expandable Multiple Contributor Accordion */}
                  {zone.reporter_name && (
                    <div className="flex flex-col gap-1.5 mt-1">
                      <div
                        onClick={(e) => hasMultipleContributors && toggleExpand(zone.id, e)}
                        className={`inline-flex items-center gap-1.5 text-slate-700 ${
                          hasMultipleContributors ? "cursor-pointer hover:text-blue-600" : ""
                        }`}
                      >
                        <UserCheck className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                        <span>
                          Reported by <strong>{zone.reporter_name}</strong>
                          {hasMultipleContributors && (
                            <span className="ml-1.5 px-1.5 py-0.5 rounded-full bg-blue-100 text-blue-700 text-[10px] font-bold">
                              +{contributors.length - 1} other{contributors.length - 1 > 1 ? "s" : ""}
                            </span>
                          )}
                        </span>
                        {hasMultipleContributors && (
                          isExpanded ? <ChevronUp className="w-3.5 h-3.5 text-blue-600 ml-0.5" /> : <ChevronDown className="w-3.5 h-3.5 text-gray-400 ml-0.5" />
                        )}
                      </div>

                      {/* Expandable Contributors Drawer */}
                      <AnimatePresence>
                        {isExpanded && hasMultipleContributors && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.25, ease: "easeInOut" }}
                            className="overflow-hidden mt-2"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <div className="pt-2 border-t border-slate-100 flex flex-col gap-2">
                              <div className="flex items-center justify-between text-[11px] text-slate-500 font-semibold px-0.5">
                                <span className="flex items-center gap-1.5 text-slate-700">
                                  <Shield className="w-3.5 h-3.5 text-blue-500" />
                                  {contributors.length} Merged Community Reports
                                </span>
                                <span className="text-[10px] font-normal text-slate-400">Chronological</span>
                              </div>

                              {/* Individual Contributor Cards with Distinct Borders, Hover Effects, and Click Interactivity */}
                              <div className="flex flex-col gap-2">
                                {contributors.map((c, idx) => {
                                  const isContributorActive = selectedContributorId === c.report_id;
                                  return (
                                    <div
                                      key={c.report_id}
                                      onClick={(e) => handleContributorClick(c.report_id, zone, e)}
                                      title={isContributorActive ? "Click to restore merged avoidance zone" : "Click to view this user's original report on map"}
                                      className={`p-2.5 rounded-lg border transition-all cursor-pointer ${
                                        isContributorActive
                                          ? "bg-blue-50/90 border-blue-500 ring-2 ring-blue-500/40 shadow-sm"
                                          : c.is_primary
                                            ? "bg-blue-50/30 border-blue-200/80 hover:bg-blue-50/70 hover:border-blue-300"
                                            : "bg-slate-50/70 border-slate-200/70 hover:bg-slate-100/90 hover:border-slate-300"
                                      }`}
                                    >
                                      {/* Header: User Info & Timestamp */}
                                      <div className="flex items-center justify-between gap-2 mb-1.5">
                                        <div className="flex items-center gap-2">
                                          <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                                            isContributorActive
                                              ? "bg-blue-600 text-white ring-2 ring-blue-300"
                                              : c.is_primary ? "bg-blue-600 text-white" : "bg-slate-200 text-slate-700"
                                          }`}>
                                            {c.reporter_name.charAt(0).toUpperCase()}
                                          </div>
                                          <div className="flex items-center gap-1.5">
                                            <span className="font-semibold text-slate-900 text-xs">{c.reporter_name}</span>
                                            {c.is_primary ? (
                                              <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[9px] font-bold tracking-wide uppercase">
                                                Primary
                                              </span>
                                            ) : (
                                              <span className="px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded text-[9px] font-medium">
                                                Merged #{c.report_id}
                                              </span>
                                            )}
                                          </div>
                                        </div>
                                        
                                        <div className="flex items-center gap-1.5">
                                          {isContributorActive && (
                                            <span className="px-1.5 py-0.5 bg-blue-600 text-white rounded text-[9px] font-bold tracking-wide uppercase animate-pulse">
                                              Inspecting Map
                                            </span>
                                          )}
                                          <span className="text-[10px] text-slate-400 font-medium">
                                            {new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                          </span>
                                        </div>
                                      </div>

                                      {/* Report Text Quote */}
                                      <p className="text-xs text-slate-700 leading-relaxed font-normal pl-7 mb-1.5">
                                        "{c.raw_text}"
                                      </p>

                                      {/* Metadata Badges Footer */}
                                      <div className="flex items-center gap-3 text-[10px] text-slate-500 pl-7">
                                        <span className="flex items-center gap-1">
                                          <span className={`w-1.5 h-1.5 rounded-full ${c.reporter_trust_score >= 80 ? 'bg-emerald-500' : 'bg-amber-500'}`} />
                                          Trust: <strong className="text-slate-700">{c.reporter_trust_score}%</strong>
                                        </span>
                                        {c.depth && (
                                          <span className="text-slate-400">
                                            Depth: <strong className="text-slate-700">{c.depth}</strong>
                                          </span>
                                        )}
                                        {c.severity && (
                                          <span className="text-slate-400 capitalize">
                                            Severity: <strong className="text-slate-700">{c.severity}</strong>
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-end gap-2 pt-3 border-t border-gray-100" onClick={(e) => e.stopPropagation()}>
                  {zone.is_active && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setConfirmId(zone.id)}
                      className="h-7 text-xs px-3 border-red-200 text-red-600 hover:bg-red-50"
                    >
                      Deactivate
                    </Button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Pagination */}
      <div className="p-3 border-t border-gray-200 bg-white">
        <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
      </div>
    </>
  );
}
