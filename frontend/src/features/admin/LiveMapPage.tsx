"use client";

import { useState, useEffect, useRef } from "react";
import { useSearchParams, usePathname } from "next/navigation";
import type { Map } from "maplibre-gl";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";
import { 
  getZones, deactivateZone, deactivateZonesBulk, AvoidanceZone,
  getPendingReports, approveReport, rejectReport, getNearbyZones,
  createOfficialZone,
  FloodReport, NearbyZone
} from "./adminApi";
import { Button } from "@/shared/ui/Button";
import { Modal } from "@/shared/ui/Modal";
import { Pagination, Tabs } from "@/shared/ui";
import BaseMap from "@/shared/ui/BaseMap";
import { useCityBoundaries } from "@/features/map/hooks/useCityBoundaries";
import { useFloodZonesLayer } from "@/features/map/hooks/useFloodZonesLayer";
import { usePendingReportsLayer } from "@/features/map/hooks/usePendingReportsLayer";
import { computeCenterCoordinate, flyToFeature, flyToCoordinates } from "@/features/map/mapGeoUtils";
import { 
  Loader2, Trash2, ShieldAlert, 
  RefreshCw, Info, AlertTriangle, CheckCircle, Clock, 
  Download, FileQuestion, ArrowRight, Merge, Check, X,
  MapPin, UserCheck, Shield
} from "lucide-react";
import { AnalyticsPanel } from "@/features/analytics/AnalyticsPanel";
import { PendingReportsPanel } from "./components/PendingReportsPanel";
import { ActiveZonesPanel } from "./components/ActiveZonesPanel";
import { ReportDetailsModal } from "./components/ReportDetailsModal";
import { CreateOfficialZonePanel } from "./components/CreateOfficialZonePanel";
import { MapProvider } from "@/features/map/MapContext";
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
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  
  // Tab State: 'pending' (Tab 1) | 'zones' (Tab 2)
  const [activeTab, setActiveTab] = useState<"pending" | "zones">("pending");
  
  // Pending Moderation State
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);
  const [isolatedReportId, setIsolatedReportId] = useState<number | null>(null);
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
  const [selectedZoneId, setSelectedZoneId] = useState<number | null>(null);
  const [selectedContributorId, setSelectedContributorId] = useState<number | null>(null);
  const [confirmId, setConfirmId] = useState<number | null>(null);
  const [batchSelectedIds, setBatchSelectedIds] = useState<number[]>([]);
  const [infoModalReport, setInfoModalReport] = useState<FloodReport | null>(null);
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

  // Track last focused query to avoid duplicate re-flying
  const lastFocusedParamRef = useRef<string | null>(null);

  // Read focus_report_id and coordinate params from URL query parameters (when redirected from Reports Page)
  useEffect(() => {
    if (!mapInstance || !isLoaded) return;

    const focusId = searchParams.get("focus_report_id");
    const tabParam = searchParams.get("tab");
    const latStr = searchParams.get("lat");
    const lngStr = searchParams.get("lng");
    const zoomStr = searchParams.get("zoom");

    const queryKey = `${focusId}_${tabParam}_${latStr}_${lngStr}`;
    if (!focusId && !latStr && !lngStr) return;

    if (tabParam === "zones" || tabParam === "pending") {
      setActiveTab(tabParam);
    }

    if (lastFocusedParamRef.current === queryKey) return;
    lastFocusedParamRef.current = queryKey;

    const executeFocus = () => {
      // 1. Direct coordinates passed from Reports Page
      if (latStr && lngStr) {
        const lat = parseFloat(latStr);
        const lng = parseFloat(lngStr);
        const zoom = zoomStr ? parseFloat(zoomStr) : 16;
        if (!isNaN(lat) && !isNaN(lng)) {
          flyToCoordinates(mapInstance, [lng, lat], { zoom, pitch: 45, duration: 1500 });
        }
      }

      // 2. Select report / zone in state
      if (focusId) {
        const idNum = Number(focusId);
        const targetPending = pendingReports?.find((r) => r.id === idNum);
        if (targetPending) {
          setActiveTab("pending");
          setSelectedReportId(idNum);
          setIsolatedReportId(idNum);

          if (targetPending.geometry && (!latStr || !lngStr)) {
            flyToFeature(mapInstance, targetPending.geometry, null, { zoom: 16, pitch: 45, duration: 1500 });
          }
        } else {
          const targetZone = (mapZones || []).find(
            (z: any) => z.report_id === idNum || (z.contributors || []).some((c: any) => c.report_id === idNum)
          );
          if (targetZone) {
            setActiveTab("zones");
            setSelectedZoneId(targetZone.id);
            if (targetZone.geometry && (!latStr || !lngStr)) {
              flyToFeature(mapInstance, targetZone.geometry, targetZone.report_geometry, { zoom: 16, pitch: 45, duration: 1500 });
            }
          }
        }
      }
    };

    // Small delay ensures MapLibre terrain and canvas resizing are settled
    const timer = setTimeout(executeFocus, 250);
    return () => clearTimeout(timer);
  }, [searchParams, pendingReports, mapZones, mapInstance, isLoaded]);

  const { data: listData, isLoading: listLoading, refetch: refetchList, isPlaceholderData } = useQuery({
    queryKey: ["adminZones", page, activeOnly],
    queryFn: () => getZones(page, LIMIT, activeOnly),
    placeholderData: (prev) => prev,
    refetchInterval: 15000,
  });

  const selectedReport = pendingReports?.find((r) => r.id === selectedReportId) || null;

  // Sub-Phase 2.4: Batch candidates — other pending reports on the same barangay/location or identical geometry
  const batchCandidates: FloodReport[] = (pendingReports || []).filter(
    (r: FloodReport) => {
      if (r.id === selectedReportId) return false;
      if (selectedReport?.barangay && r.barangay === selectedReport.barangay) return true;
      // Fallback for missing barangay: match identical geometries (useful for testing duplicates)
      if (r.geometry && selectedReport?.geometry && JSON.stringify(r.geometry) === JSON.stringify(selectedReport.geometry)) return true;
      return false;
    }
  );

  // If a report is selected, only show the selected report and its batch candidates (preserving original order)
  const filteredPendingReports = selectedReportId 
    ? (pendingReports || []).filter(r => r.id === selectedReportId || batchCandidates.some(b => b.id === r.id))
    : (pendingReports || []);

  // Nearby Zones Query for the selected pending report
  const { data: nearbyZones, isLoading: nearbyLoading } = useQuery({
    queryKey: ["nearbyZones", selectedReportId],
    queryFn: () => (selectedReportId ? getNearbyZones(selectedReportId, 500) : Promise.resolve([])),
    enabled: selectedReportId !== null,
  });

  // Modular Map Layers
  useCityBoundaries(mapInstance, isLoaded);
  useFloodZonesLayer(
    mapInstance,
    isLoaded,
    mapZones,
    false,
    activeTab,
    selectedZoneId,
    setSelectedZoneId,
    selectedContributorId,
    setSelectedContributorId
  );
  usePendingReportsLayer(
    mapInstance, 
    isLoaded, 
    filteredPendingReports, 
    activeTab, 
    (id) => {
      setSelectedReportId(id);
      // Reset isolated mode if user clicks away
      if (id === null) setIsolatedReportId(null);
    }, 
    selectedReportId,
    isolatedReportId
  );

  const pathname = usePathname();

  // Resize map canvas whenever returning to the spatial operations tab
  useEffect(() => {
    if (mapInstance && isLoaded && pathname === "/admin/map") {
      setTimeout(() => {
        mapInstance.resize();
      }, 50);
    }
  }, [pathname, mapInstance, isLoaded]);

  // Fit to Pasig City bounds on first visit ONLY IF no focus query or coordinates present
  useEffect(() => {
    if (!mapInstance || !isLoaded) return;
    
    const focusId = searchParams.get("focus_report_id");
    const latStr = searchParams.get("lat");
    const lngStr = searchParams.get("lng");
    
    // If arriving with specific report or coordinates, skip default fitBounds
    if (focusId || (latStr && lngStr)) return;

    mapInstance.fitBounds(PASIG_BOUNDS, {
      padding: { top: 40, bottom: 40, left: 40, right: 40 },
      duration: 1000,
    });
  }, [mapInstance, isLoaded, searchParams]);

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

  // Fly to selected report when clicked in the list
  useEffect(() => {
    if (!mapInstance || !isLoaded || !selectedReport || !selectedReport.geometry || activeTab !== "pending") return;
    flyToFeature(mapInstance, selectedReport.geometry, null, { zoom: 16, pitch: 45, duration: 1200 });
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

  const createOfficialZoneMutation = useMutation({
    mutationFn: createOfficialZone,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminActiveZones"] });
      queryClient.invalidateQueries({ queryKey: ["activeZonesMap"] });
      refetchMap();
    }
  });

  const handleAdminSubmitZone = async (formData: FormData) => {
    // The panel gives us multipart form data (with media etc)
    // We send this exact form data to the admin zones endpoint.
    await createOfficialZoneMutation.mutateAsync(formData);
  };

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

  const flyToZone = (zone: AvoidanceZone) => {
    if (!mapInstance || !zone.geometry) return;
    try {
      flyToFeature(mapInstance, zone.geometry, zone.report_geometry, { zoom: 16, pitch: 45, duration: 1500 });
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
          <PendingReportsPanel 
            pendingLoading={pendingLoading}
            pendingReports={pendingReports}
            filteredPendingReports={filteredPendingReports}
            selectedReportId={selectedReportId}
            setSelectedReportId={setSelectedReportId}
            onInfoClick={(r) => setInfoModalReport(r)}
            batchCandidates={batchCandidates}
            batchSelectedIds={batchSelectedIds}
            setBatchSelectedIds={setBatchSelectedIds}
            nearbyZones={nearbyZones}
            setTargetZoneId={setTargetZoneId}
            setMergeModalOpen={setMergeModalOpen}
            rejectMutation={rejectMutation}
            approveMutation={approveMutation}
          />
        )}

        {/* TAB 2: ACTIVE ZONES (DETOURS & OPERATIONS) */}
        {activeTab === "zones" && (
          <ActiveZonesPanel 
            activeOnly={activeOnly}
            setActiveOnly={setActiveOnly}
            page={page}
            setPage={setPage}
            selectedIds={selectedIds}
            setSelectedIds={setSelectedIds}
            selectedZoneId={selectedZoneId}
            setSelectedZoneId={setSelectedZoneId}
            selectedContributorId={selectedContributorId}
            setSelectedContributorId={setSelectedContributorId}
            zones={zones}
            listLoading={listLoading}
            isPlaceholderData={isPlaceholderData}
            totalPages={totalPages}
            flyToZone={flyToZone}
            setConfirmId={setConfirmId}
          />
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
          onMapLoad={(map) => {
            setMapInstance(map);
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

      {/* Admin Mode - Create Official Zone Panel overlay */}
      {isLoaded && mapInstance && (
        <MapProvider>
          <CreateOfficialZonePanel 
            isOpen={true} 
            onClose={() => {}} 
            isAdminMode={true}
            onAdminSubmit={handleAdminSubmitZone}
          />
        </MapProvider>
      )}
    </div>
  );
}
