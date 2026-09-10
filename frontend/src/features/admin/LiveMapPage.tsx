"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams, usePathname } from "next/navigation";
import type { Map } from "maplibre-gl";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";
import { 
  getZones, deactivateZone, deactivateZonesBulk, AvoidanceZone,
  getPendingReports, approveReport, rejectReport,
  createOfficialZone,
  FloodReport
} from "./adminApi";
import { Button } from "@/shared/ui";
import { Modal } from "@/shared/ui";
import { Pagination, Tabs } from "@/shared/ui";
import BaseMap from "@/shared/ui/map/BaseMap";
import { useCityBoundaries } from "@/features/map/hooks/useCityBoundaries";
import { useFloodZonesLayer } from "@/features/map/hooks/useFloodZonesLayer";
import { usePendingReportsLayer } from "@/features/map/hooks/usePendingReportsLayer";
import { computeCenterCoordinate, flyToFeature, flyToCoordinates } from "@/features/map/mapGeoUtils";
import { 
  Loader2, Trash2, ShieldAlert, 
  RefreshCw, Info, AlertTriangle, CheckCircle, Clock, 
  Download, FileQuestion, ArrowRight, Check, X,
  MapPin, UserCheck, Shield, Plus,
  ChevronRight, ChevronLeft, Sparkles
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { AnalyticsPanel } from "@/features/analytics/AnalyticsPanel";
import { PendingReportsPanel } from "./components/PendingReportsPanel";
import { ActiveZonesPanel } from "./components/ActiveZonesPanel";
import { ReportDetailsModal } from "./components/ReportDetailsModal";
import { CreateOfficialZonePanel } from "./components/CreateOfficialZonePanel";
import { MergeWorkspacePanel } from "./components/merge/MergeWorkspacePanel";
import { useMergePreviewLayer } from "@/features/map/hooks/useMergePreviewLayer";
import type { MergeCandidateItem, ReportGeometry } from "./adminApi";
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

  // Merge Workspace Secondary Drawer State
  const [isMergeDrawerOpen, setIsMergeDrawerOpen] = useState(false);
  const [isMergeMobileMapVisible, setIsMergeMobileMapVisible] = useState(false);
  const [mergingReport, setMergingReport] = useState<FloodReport | null>(null);
  const [mergePreviewCandidates, setMergePreviewCandidates] = useState<MergeCandidateItem[]>([]);
  const [mergeProposedGeometry, setMergeProposedGeometry] = useState<ReportGeometry | null>(null);
  const handleMergePreviewChange = useCallback((candidates: MergeCandidateItem[], proposedGeometry: ReportGeometry | null) => {
    setMergePreviewCandidates(candidates);
    setMergeProposedGeometry(proposedGeometry);
  }, []);

  // Create Official Zone Secondary Drawer State
  const [isCreateZoneDrawerOpen, setIsCreateZoneDrawerOpen] = useState(false);

  // Map State
  const [mapInstance, setMapInstance] = useState<Map | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isAnalyticsOpen, setIsAnalyticsOpen] = useState(false);
  const [analyticsControl, setAnalyticsControl] = useState<AnalyticsControl | null>(null);

  // Responsive viewport check
  const isMobile = useMediaQuery("(max-width: 640px), (pointer: coarse)");

  // DRAWER WIDTH: Consistent standard width across secondary workspace panels
  const DRAWER_WIDTH = 440;



  // Active Zones List State
  const [page, setPage] = useState(1);
  const [activeOnly, setActiveOnly] = useState(true);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [selectedZoneId, setSelectedZoneId] = useState<number | null>(null);
  const [selectedContributorId, setSelectedContributorId] = useState<number | null>(null);
  const [confirmId, setConfirmId] = useState<number | null>(null);
  const [infoModalReport, setInfoModalReport] = useState<FloodReport | null>(null);
  const [confirmBulk, setConfirmBulk] = useState(false);
  const [editingZone, setEditingZone] = useState<AvoidanceZone | null>(null);

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
          flyToCoordinates(mapInstance, [lng, lat], { zoom, pitch: mapInstance.getPitch(), duration: 1500 });
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
            flyToFeature(mapInstance, targetPending.geometry, null, { zoom: 16, pitch: mapInstance.getPitch(), duration: 1500 });
          }
        } else {
          const targetZone = (mapZones || []).find(
            (z: any) => z.report_id === idNum || (z.contributors || []).some((c: any) => c.report_id === idNum)
          );
          if (targetZone) {
            setActiveTab("zones");
            setSelectedZoneId(targetZone.id);
            if (targetZone.geometry && (!latStr || !lngStr)) {
              flyToFeature(mapInstance, targetZone.geometry, targetZone.report_geometry, { zoom: 16, pitch: mapInstance.getPitch(), duration: 1500 });
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

  const openMergeWorkspace = (report: FloodReport) => {
    setIsCreateZoneDrawerOpen(false);
    setMergingReport(report);
    setSelectedReportId(report.id);
    setIsolatedReportId(report.id);
    setIsMergeMobileMapVisible(false);
    setIsMergeDrawerOpen(true);
  };

  const openCreateZoneWorkspace = () => {
    setIsMergeDrawerOpen(false);
    setIsMergeMobileMapVisible(false);
    setMergePreviewCandidates([]);
    setMergeProposedGeometry(null);
    setIsolatedReportId(null);
    setEditingZone(null);
    setIsCreateZoneDrawerOpen(true);
  };

  const handleReportFocusChange = useCallback((id: number | null) => {
    setSelectedReportId(id);

    if (id === null) {
      setIsolatedReportId(null);
      setIsMergeDrawerOpen(false);
      setMergingReport(null);
      setMergePreviewCandidates([]);
      setMergeProposedGeometry(null);
      return;
    }

    const nextReport = pendingReports?.find((report) => report.id === id);
    const willShowMergeWorkspace = isMergeDrawerOpen || Boolean(mergingReport && nextReport && isCreateZoneDrawerOpen);
    if (mergingReport && nextReport && nextReport.id !== mergingReport.id) {
      setMergingReport(nextReport);
      setMergePreviewCandidates([]);
      setMergeProposedGeometry(null);
    }

    if (mergingReport && nextReport && isCreateZoneDrawerOpen) {
      setEditingZone(null);
      setIsCreateZoneDrawerOpen(false);
      setIsMergeDrawerOpen(true);
    }

    setIsolatedReportId(willShowMergeWorkspace ? id : null);
  }, [isCreateZoneDrawerOpen, isMergeDrawerOpen, mergingReport, pendingReports]);

  // Ordinary report selection never changes the queue or guesses which reports are related.
  // Map spotlight is scoped to the explicit intelligent merge workflow.
  const filteredPendingReports = pendingReports || [];
  const mapPendingReports = isMergeDrawerOpen && mergingReport
    ? filteredPendingReports.filter((report) => report.id === mergingReport.id)
    : filteredPendingReports;

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
    mapPendingReports,
    activeTab, 
    handleReportFocusChange,
    selectedReportId,
    isolatedReportId
  );
  useMergePreviewLayer({
    map: mapInstance,
    isLoaded,
    isOpen: isMergeDrawerOpen,
    primaryReport: mergingReport,
    selectedCandidates: mergePreviewCandidates,
    proposedGeometry: mergeProposedGeometry,
  });

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
    flyToFeature(mapInstance, selectedReport.geometry, null, { zoom: 16, pitch: mapInstance.getPitch(), duration: 1200 });
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
    mutationFn: ({ payload, mediaFiles }: { payload: any; mediaFiles: File[] }) =>
      createOfficialZone(payload, mediaFiles),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminActiveZones"] });
      queryClient.invalidateQueries({ queryKey: ["adminZones"] });
      queryClient.invalidateQueries({ queryKey: ["activeZonesMap"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
      refetchMap();
      refetchList();
      setIsCreateZoneDrawerOpen(false);
    }
  });

  const handleAdminSubmitZone = async (payloads: any, mediaFiles: File[] = []) => {
    if (Array.isArray(payloads)) {
      for (const p of payloads) {
        await createOfficialZoneMutation.mutateAsync({ payload: p, mediaFiles });
      }
    } else {
      await createOfficialZoneMutation.mutateAsync({ payload: payloads, mediaFiles });
    }
  };

  const handleActionControls = useCallback((map: Map) => {
    const control = new AnalyticsControl(() => setIsAnalyticsOpen(prev => !prev), false);
    map.addControl(control, "bottom-right");
    setAnalyticsControl(control);
  }, []);

  const handleMapInit = useCallback((map: Map) => {
    setMapInstance(map);
  }, []);

  const handleMapLoad = useCallback((map: Map) => {
    setMapInstance(map);
    setIsLoaded(true);
  }, []);

  useEffect(() => {
    analyticsControl?.updateState(isAnalyticsOpen);
  }, [isAnalyticsOpen, analyticsControl]);

  const zones = listData?.zones || [];
  const total = listData?.total || 0;
  const totalPages = Math.ceil(total / LIMIT);

  const handleZoneFocusChange = useCallback((id: number | null) => {
    setSelectedZoneId(id);
    if (id === null || (!isMergeDrawerOpen && !isCreateZoneDrawerOpen)) return;

    const nextZone = zones.find((zone: AvoidanceZone) => zone.id === id);
    if (!nextZone) return;

    setIsMergeDrawerOpen(false);
    setIsMergeMobileMapVisible(false);
    setMergePreviewCandidates([]);
    setMergeProposedGeometry(null);
    setIsolatedReportId(null);
    setEditingZone(nextZone);
    setIsCreateZoneDrawerOpen(true);
  }, [isCreateZoneDrawerOpen, isMergeDrawerOpen, zones]);

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
      flyToFeature(mapInstance, zone.geometry, zone.report_geometry, { zoom: 16, pitch: mapInstance.getPitch(), duration: 1500 });
    } catch (err) {
      console.error("Failed to fly to zone:", err);
    }
  };

  return (
    <MapProvider>
      <div className="flex flex-col md:flex-row h-full w-full overflow-hidden bg-white">
        {/* LEFT PANEL: Moderation & Zones Sidebar */}
        <div className={`${isMobile && isMergeDrawerOpen && isMergeMobileMapVisible ? "hidden" : "flex"} relative w-full md:w-[420px] xl:w-[460px] shrink-0 flex-col bg-white border-r border-slate-200 h-[50vh] md:flex md:h-full z-40 shadow-sm`}>
          
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
              setSelectedReportId={handleReportFocusChange}
              onInfoClick={(r) => setInfoModalReport(r)}
              onOpenMergeWorkspace={openMergeWorkspace}
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
              setSelectedZoneId={handleZoneFocusChange}
              selectedContributorId={selectedContributorId}
              setSelectedContributorId={setSelectedContributorId}
              zones={zones}
              listLoading={listLoading}
              isPlaceholderData={isPlaceholderData}
              totalPages={totalPages}
              flyToZone={flyToZone}
              setConfirmId={setConfirmId}
              onCreateOfficialZone={() => {
                openCreateZoneWorkspace();
              }}
              onEditZone={(zone) => {
                setIsMergeDrawerOpen(false);
                setMergePreviewCandidates([]);
                setMergeProposedGeometry(null);
                setIsolatedReportId(null);
                setEditingZone(zone);
                setIsCreateZoneDrawerOpen(true);
                flyToZone(zone);
              }}
            />
          )}

          {/* The Create Zone tab belongs to the primary moderation panel. */}
          {!isCreateZoneDrawerOpen && !isMergeDrawerOpen && !mergingReport && (
          <div className="absolute right-[-35px] top-3.5 z-50 hidden md:flex">
            <button
              type="button"
              onClick={openCreateZoneWorkspace}
              className="group flex h-40 w-9 flex-col items-center justify-between rounded-r-xl border border-l-0 border-slate-200 bg-white py-3 text-slate-700 shadow-[5px_4px_12px_-8px_rgba(15,23,42,0.5)] transition-all hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700"
              title="Create official zone"
            >
              <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-blue-600 text-white shadow-xs"><Plus className="h-4 w-4 stroke-[2.5]" /></div>
              <span className="my-auto select-none [writing-mode:vertical-lr] text-[10px] font-bold uppercase tracking-widest">Create zone</span>
              <ChevronRight className="h-4 w-4 text-slate-400 transition-transform group-hover:translate-x-0.5 group-hover:text-blue-600" />
            </button>
          </div>
          )}
        </div>

      {/* SECONDARY DRAWER: Merge & Spatial Operations Workspace */}
      <AnimatePresence>
        {mergingReport && (
          <motion.div
            key="merge-workspace-drawer"
            initial={{ width: 0, x: 0 }}
            animate={{
              width: isMergeDrawerOpen ? (isMobile ? "100%" : DRAWER_WIDTH) : 0,
              x: isMobile && isMergeDrawerOpen && isMergeMobileMapVisible ? "100%" : 0,
            }}
            exit={{ width: 0, x: isMobile ? "100%" : 0 }}
            transition={{
              width: { duration: 0.35, ease: [0.32, 0.72, 0, 1] },
              x: { duration: 0.25, ease: [0.32, 0.72, 0, 1] },
            }}
            className={`fixed inset-0 z-50 flex h-full shrink-0 md:relative md:inset-auto md:z-30 ${isMergeDrawerOpen ? "pointer-events-auto" : "pointer-events-none md:pointer-events-auto"}`}
            onAnimationComplete={() => {
              mapInstance?.resize();
            }}
          >
            <div className="flex h-full w-full flex-col overflow-hidden border border-slate-200 bg-white shadow-[10px_0_28px_-16px_rgba(15,23,42,0.45)]">
              <div className="flex h-full w-full min-w-0 flex-col">
                <MergeWorkspacePanel 
                  key={mergingReport.id}
                  primaryReport={mergingReport}
                  isOpen={isMergeDrawerOpen}
                  onShowMap={() => {
                    setIsMergeMobileMapVisible(true);
                    window.setTimeout(() => mapInstance?.resize(), 260);
                  }}
                  onClose={() => {
                    setIsMergeDrawerOpen(false);
                    setIsMergeMobileMapVisible(false);
                    setMergePreviewCandidates([]);
                    setMergeProposedGeometry(null);
                    setIsolatedReportId(null);
                  }}
                  mapInstance={mapInstance}
                  activeZones={mapZones || []}
                  onPreviewChange={handleMergePreviewChange}
                  onMergeSuccess={() => {
                    setIsMergeDrawerOpen(false);
                    setIsMergeMobileMapVisible(false);
                    setMergingReport(null);
                    setMergePreviewCandidates([]);
                    setMergeProposedGeometry(null);
                    setIsolatedReportId(null);
                    setSelectedReportId(null);
                    refetchPending();
                    refetchMap();
                    refetchList();
                  }}
                />
              </div>
            </div>

            {/* A collapsed workspace keeps its bookmark and report state until focus changes. */}
            {!isCreateZoneDrawerOpen && (
            <>
            <button
              type="button"
              onClick={openCreateZoneWorkspace}
              aria-pressed={false}
              className="group absolute right-[-35px] top-3.5 z-30 hidden h-40 w-9 flex-col items-center justify-between rounded-r-xl border border-l-0 border-blue-200 bg-white py-3 text-blue-700 shadow-[5px_4px_12px_-8px_rgba(15,23,42,0.5)] transition-all hover:border-blue-400 hover:bg-blue-50 md:flex"
              title="Switch to Create Zone"
            >
              <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-blue-600 text-white shadow-xs"><Plus className="h-4 w-4 stroke-[2.5]" /></div>
              <span className="my-auto select-none [writing-mode:vertical-lr] text-[10px] font-bold uppercase tracking-widest">Create zone</span>
              <ChevronRight className="h-4 w-4 text-blue-400 transition-transform group-hover:translate-x-0.5 group-hover:text-blue-700" />
            </button>

            <button
              type="button"
              onClick={() => {
                const willOpen = !isMergeDrawerOpen;
                setIsMergeDrawerOpen(willOpen);
                setIsMergeMobileMapVisible(false);
                setMergePreviewCandidates([]);
                setMergeProposedGeometry(null);
                setIsolatedReportId(willOpen ? mergingReport.id : null);
              }}
              aria-pressed={isMergeDrawerOpen}
              className={`group absolute right-[-35px] top-[11.5rem] z-30 hidden h-40 w-9 flex-col items-center justify-between rounded-r-xl border border-l-0 py-3 shadow-[5px_4px_12px_-8px_rgba(15,23,42,0.55)] transition-all md:flex ${isMergeDrawerOpen ? "border-violet-700 bg-violet-600 text-white hover:bg-violet-700" : "border-violet-200 bg-white text-violet-700 hover:border-violet-400 hover:bg-violet-50"}`}
              title={isMergeDrawerOpen ? "Collapse Review Merge drawer" : `Open Review Merge for report #${mergingReport.id}`}
            >
              <div className={`flex h-6 w-6 items-center justify-center rounded-lg ${isMergeDrawerOpen ? "bg-white/20 text-white" : "bg-violet-600 text-white shadow-xs"}`}><Sparkles className="h-4 w-4 stroke-[2.5]" /></div>
              <span className="my-auto select-none [writing-mode:vertical-lr] text-[10px] font-bold uppercase tracking-widest">Review merge</span>
              {isMergeDrawerOpen ? <ChevronLeft className="h-4 w-4 text-violet-100" /> : <ChevronRight className="h-4 w-4 text-violet-400" />}
            </button>
            </>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {isMobile && isMergeDrawerOpen && mergingReport && isMergeMobileMapVisible && (
        <Button
          type="button"
          onClick={() => setIsMergeMobileMapVisible(false)}
          className="fixed bottom-[calc(env(safe-area-inset-bottom)+1rem)] left-1/2 z-50 -translate-x-1/2 rounded-full bg-slate-900 px-4 text-xs text-white shadow-xl hover:bg-slate-800"
        >
          <MapPin className="mr-1.5 h-4 w-4" /> Return to merge
        </Button>
      )}

      {/* SECONDARY DRAWER: Create Official Zone Workspace (Pane 2) */}
      <AnimatePresence>
        {isCreateZoneDrawerOpen && (
          <motion.div
            key="create-official-zone-drawer"
            initial={{ width: 0 }}
            animate={{ width: isMobile ? "100%" : DRAWER_WIDTH }}
            exit={{ width: 0 }}
            transition={{
              width: { duration: 0.35, ease: [0.32, 0.72, 0, 1] },
            }}
            className="relative shrink-0 flex h-full z-30"
            onAnimationComplete={() => {
              mapInstance?.resize();
            }}
          >
            <div className="flex h-full w-full flex-col overflow-hidden border border-slate-200 bg-white shadow-[10px_0_28px_-16px_rgba(15,23,42,0.45)]">
              <div className="flex h-full w-full min-w-0 shrink-0 flex-col">
                <CreateOfficialZonePanel 
                  isOpen={isCreateZoneDrawerOpen} 
                  onClose={() => {
                    setIsCreateZoneDrawerOpen(false);
                    setEditingZone(null);
                  }} 
                  isAdminMode={true}
                  onAdminSubmit={handleAdminSubmitZone}
                  onZoneUpdated={() => {
                    refetchList();
                    refetchMap();
                  }}
                  editingZone={editingZone}
                  mapInstance={mapInstance}
                />
              </div>
            </div>

            {/* DRAWER COLLAPSE HANDLE (Front of drawer in your hands) */}
            <button
              type="button"
              onClick={() => {
                setIsCreateZoneDrawerOpen(false);
                setEditingZone(null);
              }}
              aria-pressed="true"
              className="group absolute right-[-35px] top-3.5 z-30 hidden h-40 w-9 flex-col items-center justify-between rounded-r-xl border border-l-0 border-blue-700 bg-blue-600 py-3 text-white shadow-[5px_4px_12px_-8px_rgba(15,23,42,0.55)] transition-all hover:bg-blue-700 md:flex"
              title="Close Create Zone drawer"
            >
              <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-white/20 text-white transition-transform group-hover:scale-105">
                <Plus className="w-4 h-4 stroke-[2.5]" />
              </div>
              <span className="my-auto select-none [writing-mode:vertical-lr] text-[10px] font-bold uppercase tracking-widest">
                CREATE ZONE
              </span>
              <ChevronLeft className="h-4 w-4 text-blue-100 transition-transform group-hover:-translate-x-0.5 group-hover:text-white" />
            </button>

            {mergingReport && (
              <button
                type="button"
                onClick={() => openMergeWorkspace(mergingReport)}
                aria-pressed={false}
                className="group absolute right-[-35px] top-[11.5rem] z-30 hidden h-40 w-9 flex-col items-center justify-between rounded-r-xl border border-l-0 border-violet-200 bg-white py-3 text-violet-700 shadow-[5px_4px_12px_-8px_rgba(15,23,42,0.5)] transition-all hover:border-violet-400 hover:bg-violet-50 md:flex"
                title={`Return to merge review for report #${mergingReport.id}`}
              >
                <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-violet-600 text-white shadow-xs"><Sparkles className="h-4 w-4 stroke-[2.5]" /></div>
                <span className="my-auto select-none [writing-mode:vertical-lr] text-[10px] font-bold uppercase tracking-widest">Review merge</span>
                <ChevronRight className="h-4 w-4 text-violet-400 transition-transform group-hover:translate-x-0.5 group-hover:text-violet-700" />
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* RIGHT PANEL: Live Map View */}
      <div className={`flex-1 relative ${isMobile && isMergeDrawerOpen && isMergeMobileMapVisible ? "h-full" : "h-[50vh]"} md:h-full bg-[#f2efe9] overflow-hidden transform-gpu z-0`}>
        <BaseMap 
          actionControls={handleActionControls}
          onMapInit={handleMapInit}
          onMapLoad={handleMapLoad}
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

      {/* Report Details Modal (Triggered by Info button) */}
      <ReportDetailsModal
        report={infoModalReport}
        isOpen={infoModalReport !== null}
        onClose={() => setInfoModalReport(null)}
        onViewOnMap={(report) => {
          setActiveTab("pending");
          setSelectedReportId(report.id);
          if (mapInstance && report.geometry) {
            flyToFeature(mapInstance, report.geometry, null, { zoom: 16, pitch: mapInstance.getPitch(), duration: 1200 });
          }
        }}
        onApprove={(id) => {
          approveMutation.mutate({ id, payload: { action: "ISOLATE" } });
          setInfoModalReport(null);
        }}
        onReject={(id) => {
          rejectMutation.mutate(id);
          setInfoModalReport(null);
        }}
        isApproveLoading={approveMutation.isPending}
        isRejectLoading={rejectMutation.isPending}
        onOpenMedia={(urls, idx) => {
          if (urls[idx]) window.open(urls[idx], "_blank");
        }}
      />
      </div>
    </MapProvider>
  );
}
