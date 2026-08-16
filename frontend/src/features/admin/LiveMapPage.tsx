"use client";

import { useState, useEffect } from "react";
import type { Map } from "maplibre-gl";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";
import { 
  getZones, deactivateZone, deactivateZonesBulk, AvoidanceZone,
  getPendingReports, approveReport, rejectReport, getNearbyZones,
  FloodReport, NearbyZone
} from "./adminApi";
import { Button } from "@/shared/ui/Button";
import { Modal } from "@/shared/ui/Modal";
import { Pagination, Tabs } from "@/shared/ui";
import BaseMap from "@/shared/ui/BaseMap";
import { useCityBoundaries } from "@/features/map/hooks/useCityBoundaries";
import { useFloodZonesLayer } from "@/features/map/hooks/useFloodZonesLayer";
import { 
  Loader2, Trash2, ShieldAlert, 
  RefreshCw, Info, AlertTriangle, CheckCircle, Clock, 
  Download, FileQuestion, ArrowRight, Merge, Check, X,
  MapPin, UserCheck, Shield
} from "lucide-react";
import { AnalyticsPanel } from "@/features/analytics/AnalyticsPanel";
import maplibregl from "maplibre-gl";

class AnalyticsControl {
  private _map: maplibregl.Map | undefined;
  private _container: HTMLDivElement | undefined;
  private _onClick: () => void;
  private _isActive: boolean;

  constructor(onClick: () => void, isActive: boolean) {
    this._onClick = onClick;
    this._isActive = isActive;
  }

  updateState(isActive: boolean) {
    this._isActive = isActive;
    if (this._container) {
      const btn = this._container.querySelector('button');
      if (btn) {
        btn.style.backgroundColor = this._isActive ? "#eff6ff" : "transparent";
      }
    }
  }

  onAdd(map: maplibregl.Map) {
    this._map = map;
    this._container = document.createElement("div");
    this._container.className = "maplibregl-ctrl maplibregl-ctrl-group";
    
    const btn = document.createElement("button");
    btn.type = "button";
    btn.title = "Toggle Analytics";
    
    btn.style.cssText = `
      align-items: center;
      justify-content: center;
      width: 48px;
      height: 48px;
      background-color: ${this._isActive ? "#eff6ff" : "transparent"};
      color: #2563eb;
      border: none;
      cursor: pointer;
      transition: background-color 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      padding: 0;
      display: flex;
    `;
    
    btn.onmouseenter = () => {
      btn.style.backgroundColor = this._isActive ? "#dbeafe" : "#f8fafc";
    };
    btn.onmouseleave = () => {
      btn.style.backgroundColor = this._isActive ? "#eff6ff" : "transparent";
    };
    
    btn.innerHTML = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>`;
    btn.onclick = this._onClick;
    
    this._container.appendChild(btn);
    return this._container;
  }

  onRemove() {
    if (this._container && this._container.parentNode) {
      this._container.parentNode.removeChild(this._container);
    }
    this._map = undefined;
  }
}

const LIMIT = 10;

// Pasig City Geographical Bounding Box
const PASIG_BOUNDS: [[number, number], [number, number]] = [
  [121.0515, 14.5338], // Southwest (Ugong / San Joaquin / boundary)
  [121.1112, 14.6235], // Northeast (Santolan / Manggahan / boundary)
];

const VIEW_STORAGE_KEY = "lanes_admin_map_viewport";

export default function LiveMapPage() {
  const queryClient = useQueryClient();
  
  // Tab State: 'pending' (Tab 1) | 'zones' (Tab 2)
  const [activeTab, setActiveTab] = useState<"pending" | "zones">("pending");
  
  // Pending Moderation State
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [targetZoneId, setTargetZoneId] = useState<number | null>(null);
  const [mergeModalOpen, setMergeModalOpen] = useState(false);

  // Map State
  const [mapInstance, setMapInstance] = useState<Map | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isAnalyticsOpen, setIsAnalyticsOpen] = useState(false);
  const [analyticsControl, setAnalyticsControl] = useState<AnalyticsControl | null>(null);

  // Active Zones List State
  const [page, setPage] = useState(1);
  const [activeOnly, setActiveOnly] = useState(true);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [confirmId, setConfirmId] = useState<number | null>(null);
  const [confirmBulk, setConfirmBulk] = useState(false);

  // Queries
  const { data: mapZones, refetch: refetchMap } = useQuery({
    queryKey: ["activeZonesMap"],
    queryFn: () => apiClient.get<any[]>("/reports/active-zones"),
    refetchInterval: 15000,
  });

  const { data: pendingReports, isLoading: pendingLoading, refetch: refetchPending } = useQuery({
    queryKey: ["adminPendingReports"],
    queryFn: getPendingReports,
    refetchInterval: 10000,
  });

  const { data: listData, isLoading: listLoading, refetch: refetchList, isPlaceholderData } = useQuery({
    queryKey: ["adminZones", page, activeOnly],
    queryFn: () => getZones(page, LIMIT, activeOnly),
    placeholderData: (prev) => prev,
    refetchInterval: 15000,
  });

  const selectedReport = pendingReports?.find((r) => r.id === selectedReportId) || null;

  // Nearby Zones Query for the selected pending report
  const { data: nearbyZones, isLoading: nearbyLoading } = useQuery({
    queryKey: ["nearbyZones", selectedReportId],
    queryFn: () => (selectedReportId ? getNearbyZones(selectedReportId, 500) : Promise.resolve([])),
    enabled: selectedReportId !== null,
  });

  // Modular Map Layers
  useCityBoundaries(mapInstance, isLoaded);
  useFloodZonesLayer(mapInstance, isLoaded, mapZones);

  // Restore previous camera position or fit to Pasig City bounds on first visit
  useEffect(() => {
    if (!mapInstance || !isLoaded) return;

    try {
      const savedViewStr = localStorage.getItem(VIEW_STORAGE_KEY);
      if (savedViewStr) {
        const saved = JSON.parse(savedViewStr);
        if (saved.center && saved.zoom) {
          mapInstance.jumpTo({
            center: saved.center,
            zoom: saved.zoom,
            pitch: saved.pitch || 0,
            bearing: saved.bearing || 0,
          });
          return;
        }
      }
    } catch (e) {
      console.warn("Failed to restore saved map viewport:", e);
    }

    // Default: Fit Pasig City completely within viewport
    mapInstance.fitBounds(PASIG_BOUNDS, {
      padding: { top: 40, bottom: 40, left: 40, right: 40 },
      duration: 1000,
    });
  }, [mapInstance, isLoaded]);

  // Save camera movements to localStorage
  useEffect(() => {
    if (!mapInstance || !isLoaded) return;

    const saveViewport = () => {
      try {
        const center = mapInstance.getCenter();
        const zoom = mapInstance.getZoom();
        const pitch = mapInstance.getPitch();
        const bearing = mapInstance.getBearing();
        localStorage.setItem(
          VIEW_STORAGE_KEY,
          JSON.stringify({
            center: [center.lng, center.lat],
            zoom,
            pitch,
            bearing,
          })
        );
      } catch (e) {
        // ignore localStorage errors
      }
    };

    mapInstance.on("moveend", saveViewport);
    return () => {
      mapInstance.off("moveend", saveViewport);
    };
  }, [mapInstance, isLoaded]);

  // Heatmap Data for Analytics
  const { data: heatmapData } = useQuery({
    queryKey: ["analytics", "heatmap"],
    queryFn: () => apiClient.get<any>("/analytics/heatmap"),
    enabled: isAnalyticsOpen,
  });

  // Stats Data for CSV Export
  const { data: statsData, isLoading: isStatsLoading } = useQuery({
    queryKey: ["analyticsStats"],
    queryFn: () => apiClient.get<any>("/analytics/stats"),
    enabled: isAnalyticsOpen,
  });

  // Heatmap Layer Effect
  useEffect(() => {
    if (!isLoaded || !mapInstance) return;
    const map = mapInstance;
    if (!map.style) return;
    
    if (map.getLayer("heatmap-layer")) map.removeLayer("heatmap-layer");
    if (map.getSource("heatmap-source")) map.removeSource("heatmap-source");

    if (!isAnalyticsOpen || !heatmapData || !heatmapData.features || heatmapData.features.length === 0) return;

    map.addSource("heatmap-source", {
      type: "geojson",
      data: heatmapData
    });

    map.addLayer({
      id: "heatmap-layer",
      type: "heatmap",
      source: "heatmap-source",
      maxzoom: 15,
      paint: {
        "heatmap-weight": ["get", "weight"],
        "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 0, 1, 15, 3],
        "heatmap-color": [
          "interpolate",
          ["linear"],
          ["heatmap-density"],
          0, "rgba(0, 0, 255, 0)",
          0.2, "royalblue",
          0.4, "cyan",
          0.6, "lime",
          0.8, "yellow",
          1, "red"
        ],
        "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 0, 2, 15, 20],
        "heatmap-opacity": ["interpolate", ["linear"], ["zoom"], 13, 0.8, 15, 0]
      }
    });
  }, [heatmapData, isLoaded, isAnalyticsOpen, mapInstance]);

  // Selected Pending Report Preview Layer on Map (Transparent Buffer Only, No Pins/Solid Lines)
  useEffect(() => {
    if (!mapInstance || !isLoaded || !mapInstance.style) return;

    // Clean up existing preview layers
    if (mapInstance.getLayer("pending-preview-layer")) mapInstance.removeLayer("pending-preview-layer");
    if (mapInstance.getLayer("pending-preview-outline")) mapInstance.removeLayer("pending-preview-outline");
    if (mapInstance.getSource("pending-preview-source")) mapInstance.removeSource("pending-preview-source");

    if (!selectedReport || !selectedReport.geometry || activeTab !== "pending") return;

    const isLine = selectedReport.geometry.type === "LineString";
    
    // Create preview buffer geometry approximation or bounding box
    let feature: any = null;
    if (isLine) {
      const coords = selectedReport.geometry.coordinates;
      // Fly to start coord
      mapInstance.flyTo({ center: coords[0] as [number, number], zoom: 16, duration: 1200 });
      feature = {
        type: "Feature",
        geometry: selectedReport.geometry,
        properties: { severity: selectedReport.severity }
      };
    } else if (selectedReport.geometry.type === "Point") {
      const coords = selectedReport.geometry.coordinates;
      mapInstance.flyTo({ center: coords as [number, number], zoom: 16, duration: 1200 });
      feature = {
        type: "Feature",
        geometry: selectedReport.geometry,
        properties: { severity: selectedReport.severity }
      };
    }

    if (feature) {
      mapInstance.addSource("pending-preview-source", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: [feature]
        }
      });

      // Semi-transparent dashed outline
      mapInstance.addLayer({
        id: "pending-preview-outline",
        type: "line",
        source: "pending-preview-source",
        paint: {
          "line-color": "#f59e0b",
          "line-width": 18,
          "line-opacity": 0.35,
          "line-dasharray": [2, 1]
        }
      });
    }
  }, [selectedReport, activeTab, isLoaded, mapInstance]);

  // Mutations
  const approveMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload?: any }) => approveReport(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminPendingReports"] });
      queryClient.invalidateQueries({ queryKey: ["adminZones"] });
      queryClient.invalidateQueries({ queryKey: ["activeZonesMap"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
      setSelectedReportId(null);
      setMergeModalOpen(false);
    }
  });

  const rejectMutation = useMutation({
    mutationFn: (id: number) => rejectReport(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminPendingReports"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
      setSelectedReportId(null);
    }
  });

  const deactivateSingleMutation = useMutation({
    mutationFn: (id: number) => deactivateZone(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminZones"] });
      queryClient.invalidateQueries({ queryKey: ["activeZonesMap"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
      setConfirmId(null);
    },
  });

  const deactivateBulkMutation = useMutation({
    mutationFn: (ids: number[]) => deactivateZonesBulk(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminZones"] });
      queryClient.invalidateQueries({ queryKey: ["activeZonesMap"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
      setSelectedIds([]);
      setConfirmBulk(false);
    },
  });

  const zones = listData?.zones || [];
  const total = listData?.total || 0;
  const totalPages = Math.ceil(total / LIMIT);

  const handleExportCSV = () => {
    if (!statsData) return;
    let csv = "Type,Name,Alert Count\n";
    statsData.top_barangays?.forEach((b: any) => {
      csv += `Barangay,${b.barangay || "Unknown"},${b.count}\n`;
    });
    statsData.top_locations?.forEach((l: any) => {
      csv += `Location,${l.location || "Unknown"},${l.count}\n`;
    });
    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.setAttribute("hidden", "");
    a.setAttribute("href", url);
    a.setAttribute("download", "lanes_analytics_export.csv");
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      const activeIdsInPage = zones.filter((z: AvoidanceZone) => z.is_active).map((z: AvoidanceZone) => z.id);
      setSelectedIds(activeIdsInPage);
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectRow = (id: number, checked: boolean) => {
    if (checked) setSelectedIds((prev) => [...prev, id]);
    else setSelectedIds((prev) => prev.filter((item) => item !== id));
  };

  const flyToZone = (zone: AvoidanceZone) => {
    if (!mapInstance || !zone.geometry || !zone.geometry.coordinates) return;
    try {
      const rings = zone.geometry.coordinates[0];
      if (!rings || rings.length === 0) return;
      let sumLng = 0; let sumLat = 0;
      rings.forEach(coord => { sumLng += coord[0]; sumLat += coord[1]; });
      const center: [number, number] = [sumLng / rings.length, sumLat / rings.length];
      
      mapInstance.flyTo({
        center,
        zoom: 16,
        pitch: 45,
        duration: 1500
      });
    } catch (err) {
      console.error("Failed to fly to zone:", err);
    }
  };

  return (
    <div className="flex flex-col md:flex-row h-full w-full overflow-hidden bg-white">
      {/* LEFT PANEL: Moderation & Zones Sidebar */}
      <div className="w-full md:w-[420px] xl:w-[460px] shrink-0 flex flex-col bg-white border-r border-slate-200 h-[50vh] md:h-full z-10 shadow-sm">
        
        {/* Mode Switcher Tabs Header */}
        <div className="p-3 border-b border-gray-100 bg-slate-50/70 flex items-center justify-between gap-2">
          <div className="flex-1">
            <Tabs<"pending" | "zones">
              tabs={[
                {
                  id: "pending",
                  label: "Pending Reports",
                  icon: FileQuestion,
                  badge: pendingReports && pendingReports.length > 0 ? pendingReports.length : undefined,
                  badgeColor: "bg-amber-500 text-white"
                },
                {
                  id: "zones",
                  label: "Active Zones",
                  icon: ShieldAlert,
                  badge: total > 0 ? total : undefined,
                  badgeColor: "bg-emerald-100 text-emerald-700"
                }
              ]}
              activeTab={activeTab}
              onChange={(tab) => setActiveTab(tab)}
              variant="segmented"
            />
          </div>

          <Button 
            variant="outline" 
            size="sm"
            onClick={() => { refetchPending(); refetchList(); refetchMap(); }}
            className="h-9 px-2.5 rounded-xl shrink-0 bg-white"
            title="Refresh list"
          >
            <RefreshCw className="w-3.5 h-3.5 text-gray-600" />
          </Button>
        </div>

        {/* TAB 1: PENDING REPORTS (MODERATION QUEUE) */}
        {activeTab === "pending" && (
          <div className="flex-1 overflow-y-auto divide-y divide-gray-100">
            {pendingLoading ? (
              <div className="flex flex-col items-center justify-center h-48 text-gray-400 gap-2">
                <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                <span className="text-xs font-medium">Checking moderation queue...</span>
              </div>
            ) : !pendingReports || pendingReports.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-48 text-gray-400 gap-2 p-6 text-center">
                <CheckCircle className="w-8 h-8 text-emerald-500" />
                <span className="text-sm font-semibold text-gray-700">Queue is Clear</span>
                <p className="text-xs text-gray-400">No unapproved flood reports require moderation.</p>
              </div>
            ) : (
              pendingReports.map((report: FloodReport) => {
                const isSelected = selectedReportId === report.id;
                const hasNearby = isSelected && nearbyZones && nearbyZones.length > 0;

                return (
                  <div
                    key={report.id}
                    onClick={() => setSelectedReportId(report.id)}
                    className={`p-4 transition-all cursor-pointer hover:bg-slate-50/80 ${
                      isSelected ? "bg-blue-50/50 ring-2 ring-blue-500/20" : ""
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-gray-900">Report #{report.id}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wide ${
                          report.severity === "high" || report.severity === "extreme"
                            ? "bg-red-100 text-red-700"
                            : "bg-amber-100 text-amber-700"
                        }`}>
                          {report.severity}
                        </span>
                        {report.depth && (
                          <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-700 text-[10px] font-medium">
                            {report.depth}
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] text-gray-400 font-medium">
                        {new Date(report.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>

                    <p className="text-xs text-slate-700 font-medium line-clamp-2 mb-2">
                      "{report.raw_text}"
                    </p>

                    <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-3">
                      <MapPin className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                      <span className="truncate">{report.barangay ? `Brgy. ${report.barangay}, Pasig` : "Pasig City"}</span>
                    </div>

                    {/* Nearby Zone Alert Badge */}
                    {hasNearby && (
                      <div className="mb-3 p-2.5 bg-amber-50 border border-amber-200/70 rounded-xl flex items-center justify-between text-xs text-amber-800 animate-fade-in">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                          <span>Nearby Active Zone ({nearbyZones[0].distance_meters}m away)</span>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => {
                            e.stopPropagation();
                            setTargetZoneId(nearbyZones[0].id);
                            setMergeModalOpen(true);
                          }}
                          className="h-6 text-[11px] px-2 border-amber-300 bg-white hover:bg-amber-100 text-amber-900"
                        >
                          <Merge className="w-3 h-3 mr-1" /> Merge
                        </Button>
                      </div>
                    )}

                    {/* Quick Moderation Actions */}
                    <div className="flex items-center justify-end gap-2 pt-2 border-t border-gray-100" onClick={(e) => e.stopPropagation()}>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => rejectMutation.mutate(report.id)}
                        disabled={rejectMutation.isPending}
                        className="h-7 text-xs px-2.5 text-gray-600 hover:bg-gray-100 rounded-lg"
                      >
                        <X className="w-3.5 h-3.5 mr-1 text-red-500" /> Reject
                      </Button>
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => approveMutation.mutate({ id: report.id, payload: { action: "CREATE_NEW" } })}
                        disabled={approveMutation.isPending}
                        className="h-7 text-xs px-3 rounded-lg shadow-sm"
                      >
                        <Check className="w-3.5 h-3.5 mr-1" /> Approve as New Zone
                      </Button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* TAB 2: ACTIVE ZONES (DETOURS & OPERATIONS) */}
        {activeTab === "zones" && (
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
                zones.map((zone: AvoidanceZone) => (
                  <div
                    key={zone.id}
                    onClick={() => flyToZone(zone)}
                    className={`p-4 transition-colors cursor-pointer hover:bg-slate-50/80 ${selectedIds.includes(zone.id) ? "bg-blue-50/40" : ""}`}
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
                      {zone.reporter_name && (
                        <div className="flex items-center gap-1.5 text-slate-500">
                          <UserCheck className="w-3.5 h-3.5 text-blue-500" />
                          <span>Reported by <strong>{zone.reporter_name}</strong></span>
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
                ))
              )}
            </div>

            {/* Pagination */}
            <div className="p-3 border-t border-gray-200 bg-white">
              <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
            </div>
          </>
        )}
      </div>

      {/* RIGHT PANEL: Live Map View */}
      <div className="flex-1 relative h-[50vh] md:h-full bg-slate-100 overflow-hidden">
        <BaseMap 
          actionControls={(map) => {
            const control = new AnalyticsControl(() => setIsAnalyticsOpen(prev => !prev), isAnalyticsOpen);
            map.addControl(control, "bottom-right");
            setAnalyticsControl(control);
          }}
          onMapInit={(map) => {
            setMapInstance(map);
          }}
          onMapLoad={() => {
            setIsLoaded(true);
          }}
        >
          {/* Floating Analytics Panel */}
          {isAnalyticsOpen && (
            <>
              <AnalyticsPanel
                isOpen={isAnalyticsOpen}
                onClose={() => setIsAnalyticsOpen(false)}
              />
              <div className="absolute top-4 right-4 z-20 pointer-events-auto">
                <Button 
                  onClick={handleExportCSV} 
                  disabled={isStatsLoading || !statsData}
                  className="flex items-center gap-2 bg-white text-slate-700 hover:bg-slate-50 border border-slate-200 shadow-md text-xs font-semibold py-2 px-3.5 h-auto rounded-xl"
                >
                  <Download className="w-4 h-4 text-blue-600" />
                  Export to CSV
                </Button>
              </div>
            </>
          )}

          {/* Bulk Actions Float (Over Map) */}
          {selectedIds.length > 0 && (
            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-white/95 text-slate-800 py-2.5 px-5 rounded-2xl flex items-center gap-5 shadow-2xl border border-slate-200/80 backdrop-blur-md z-30 animate-fade-in pointer-events-auto">
              <span className="text-xs font-semibold text-slate-700">
                Selected <span className="text-blue-600 font-bold">{selectedIds.length}</span> {selectedIds.length === 1 ? "zone" : "zones"}
              </span>
              <div className="flex items-center gap-2">
                <Button 
                  onClick={() => setConfirmBulk(true)} 
                  variant="danger" 
                  size="sm" 
                  className="rounded-xl font-medium gap-1.5 shadow-sm"
                >
                  <Trash2 className="w-3.5 h-3.5" /> Deactivate Selected
                </Button>
                <Button 
                  onClick={() => setSelectedIds([])} 
                  variant="outline" 
                  size="sm" 
                  className="rounded-xl font-medium"
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </BaseMap>
      </div>

      {/* Confirmation Modal for Single Deactivation */}
      <Modal isOpen={confirmId !== null} onClose={() => setConfirmId(null)} title="Confirm Deactivation">
        <div className="space-y-4 text-sm text-gray-600">
          <div className="flex items-start gap-3 p-3 bg-amber-50 rounded-xl border border-amber-100 text-amber-800">
            <Info className="w-5 h-5 shrink-0 mt-0.5" />
            <p>Deactivating this detour zone will remove the routing block. All route calculations will pass through this coordinate area.</p>
          </div>
          <p>Are you sure you want to deactivate detour zone <strong>#{confirmId}</strong>?</p>
          <div className="flex justify-end gap-2.5 pt-2">
            <Button variant="outline" size="sm" onClick={() => setConfirmId(null)} className="rounded-xl">Cancel</Button>
            <Button 
              variant="danger" 
              size="sm"
              onClick={() => confirmId && deactivateSingleMutation.mutate(confirmId)} 
              disabled={deactivateSingleMutation.isPending} 
              className="rounded-xl"
            >
              {deactivateSingleMutation.isPending ? "Deactivating..." : "Deactivate Zone"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Confirmation Modal for Bulk Deactivation */}
      <Modal isOpen={confirmBulk} onClose={() => setConfirmBulk(false)} title="Confirm Bulk Deactivation">
        <div className="space-y-4 text-sm text-gray-600">
          <div className="flex items-start gap-3 p-3 bg-amber-50 rounded-xl border border-amber-100 text-amber-800">
            <Info className="w-5 h-5 shrink-0 mt-0.5" />
            <p>Deactivating multiple detour zones simultaneously will lift all routing blocks for the selected areas.</p>
          </div>
          <p>Are you sure you want to deactivate <strong>{selectedIds.length}</strong> selected detour zones?</p>
          <div className="flex justify-end gap-2.5 pt-2">
            <Button variant="outline" size="sm" onClick={() => setConfirmBulk(false)} className="rounded-xl">Cancel</Button>
            <Button 
              variant="danger" 
              size="sm"
              onClick={() => deactivateBulkMutation.mutate(selectedIds)} 
              disabled={deactivateBulkMutation.isPending} 
              className="rounded-xl"
            >
              {deactivateBulkMutation.isPending ? "Deactivating..." : "Deactivate Selected"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Merge Confirmation Modal */}
      <Modal isOpen={mergeModalOpen} onClose={() => setMergeModalOpen(false)} title="Confirm Spatial Merge">
        <div className="space-y-4 text-sm text-gray-600">
          <div className="flex items-start gap-3 p-3 bg-blue-50 rounded-xl border border-blue-100 text-blue-800">
            <Merge className="w-5 h-5 shrink-0 mt-0.5" />
            <p>Merging will attach Report <strong>#{selectedReportId}</strong> into active Zone <strong>#{targetZoneId}</strong>. Both reporters will receive full Trust Score credit without creating a duplicate routing barrier.</p>
          </div>
          <div className="flex justify-end gap-2.5 pt-2">
            <Button variant="outline" size="sm" onClick={() => setMergeModalOpen(false)} className="rounded-xl">Cancel</Button>
            <Button 
              variant="primary" 
              size="sm"
              onClick={() => selectedReportId && targetZoneId && approveMutation.mutate({
                id: selectedReportId,
                payload: { action: "MERGE", target_zone_id: targetZoneId }
              })} 
              disabled={approveMutation.isPending} 
              className="rounded-xl"
            >
              {approveMutation.isPending ? "Merging..." : "Confirm & Merge"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
