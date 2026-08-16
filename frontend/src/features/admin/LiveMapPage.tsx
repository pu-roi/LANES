"use client";

import { useState, useEffect } from "react";
import type { Map } from "maplibre-gl";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";
import { getZones, deactivateZone, deactivateZonesBulk, AvoidanceZone } from "./adminApi";
import { Button } from "@/shared/ui/Button";
import { Modal } from "@/shared/ui/Modal";
import { Pagination } from "@/shared/ui";
import BaseMap from "@/shared/ui/BaseMap";
import { useCityBoundaries } from "@/features/map/hooks/useCityBoundaries";
import { useFloodZonesLayer } from "@/features/map/hooks/useFloodZonesLayer";
import { 
  Loader2, Map as MapIcon, Trash2, ShieldAlert, Layers, 
  RefreshCw, Info, AlertTriangle, CheckCircle, Check, Clock, X, TrendingUp, Download
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

export default function LiveMapPage() {
  const queryClient = useQueryClient();
  
  // Map State
  const [mapInstance, setMapInstance] = useState<Map | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [isAnalyticsOpen, setIsAnalyticsOpen] = useState(false);
  const [analyticsControl, setAnalyticsControl] = useState<AnalyticsControl | null>(null);

  // List State
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

  // Modular Map Layers
  useCityBoundaries(mapInstance, isLoaded);
  useFloodZonesLayer(mapInstance, isLoaded, mapZones);

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

  // Heatmap Layer Logic
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

  // Update control state when isAnalyticsOpen changes
  useEffect(() => {
    if (analyticsControl) {
      analyticsControl.updateState(isAnalyticsOpen);
    }
  }, [isAnalyticsOpen, analyticsControl]);

  const { data: listData, isLoading: listLoading, refetch: refetchList, isPlaceholderData } = useQuery({
    queryKey: ["adminZones", page, activeOnly],
    queryFn: () => getZones(page, LIMIT, activeOnly),
    placeholderData: (prev) => prev,
    refetchInterval: 15000,
  });

  const zones = listData?.zones || [];
  const total = listData?.total || 0;
  const totalPages = Math.ceil(total / LIMIT);

  // Mutations
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

  // List Handlers
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
    <div className="flex flex-col md:flex-row gap-6 h-full">
      {/* LEFT PANEL: Zones List */}
      <div className="w-full md:w-[400px] xl:w-[450px] shrink-0 flex flex-col bg-white border border-gray-200 rounded-xl shadow-sm h-[50vh] md:h-[calc(100vh-6rem)] overflow-hidden">
        <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-slate-50/50">
          <div>
            <h1 className="text-lg font-bold text-gray-900 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-500" /> Detour & Flood Zones
            </h1>
            <p className="text-xs text-gray-500 mt-0.5">Active routing barriers enforced across Pasig City</p>
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => { refetchList(); refetchMap(); }}
            className="h-8 px-2 text-xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </Button>
        </div>

        {/* Filter Toolbar */}
        <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-white gap-2">
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

        {/* List Content */}
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
            <>
              {zones.map((zone: AvoidanceZone) => (
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
                        <p className="text-xs text-gray-500 mt-0.5 font-medium">Report #{zone.report_id}</p>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1.5 text-xs text-gray-600 pl-7 mb-3">
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-gray-400" />
                      Created: {new Date(zone.created_at).toLocaleDateString()} {new Date(zone.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                    </div>
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
              ))}
            </>
          )}
        </div>

        {/* Pagination */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
        </div>
      </div>

      {/* RIGHT PANEL: Map View */}
      <div className="flex-1 relative rounded-xl overflow-hidden border border-gray-200 shadow-sm h-[50vh] md:h-[calc(100vh-6rem)] bg-slate-100">
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
          {/* Floating Analytics Panel (Over Map) */}
          {isAnalyticsOpen && (
            <>
              <AnalyticsPanel
                isOpen={isAnalyticsOpen}
                onClose={() => setIsAnalyticsOpen(false)}
              />
              {/* Export Button (Top Right of Map) */}
              <div className="absolute top-4 right-4 z-20 pointer-events-auto">
                <Button 
                  onClick={handleExportCSV} 
                  disabled={isStatsLoading || !statsData}
                  className="flex items-center gap-2 bg-white text-slate-700 hover:bg-slate-50 border border-slate-200 shadow-md hover:shadow-lg transition-all text-xs font-semibold py-2 px-3.5 h-auto rounded-xl"
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

      {/* Confirmation Modals */}
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
    </div>
  );
}
