"use client";

import { useState } from "react";
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
  RefreshCw, Info, AlertTriangle, CheckCircle, Check, Clock 
} from "lucide-react";

const LIMIT = 10;

export default function LiveMapPage() {
  const queryClient = useQueryClient();
  
  // Map State
  const [mapInstance, setMapInstance] = useState<Map | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

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
    <div className="w-full h-full flex flex-col md:flex-row gap-6">
      {/* LEFT PANEL: Active Zones Table */}
      <div className="w-full md:w-[480px] flex flex-col bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden shrink-0 h-[50vh] md:h-[calc(100vh-6rem)]">
        {/* Header */}
        <div className="p-5 border-b border-gray-100 flex items-center justify-between bg-slate-50/50">
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
          onMapInit={(map) => {
            setMapInstance(map);
          }}
          onMapLoad={() => {
            setIsLoaded(true);
          }}
        >
          {/* Bulk Actions Float (Over Map) */}
          {selectedIds.length > 0 && (
            <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-slate-900/95 text-white py-3 px-6 rounded-2xl flex items-center gap-6 shadow-xl border border-slate-800 backdrop-blur-sm z-30 animate-fade-in pointer-events-auto">
              <span className="text-sm font-semibold">
                Selected <span className="text-blue-400 font-extrabold">{selectedIds.length}</span> zones
              </span>
              <div className="flex gap-2">
                <Button onClick={() => setConfirmBulk(true)} className="bg-red-600 hover:bg-red-700 text-white text-xs font-semibold px-4 py-1.5 h-8">
                  <Trash2 className="w-3.5 h-3.5 mr-1.5" /> Deactivate Selected
                </Button>
                <Button onClick={() => setSelectedIds([])} variant="outline" className="text-slate-300 border-slate-700 hover:bg-slate-800 text-xs font-semibold px-3 h-8">
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
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" onClick={() => setConfirmId(null)}>Cancel</Button>
            <Button onClick={() => confirmId && deactivateSingleMutation.mutate(confirmId)} disabled={deactivateSingleMutation.isPending} className="bg-red-600 text-white">
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
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" onClick={() => setConfirmBulk(false)}>Cancel</Button>
            <Button onClick={() => deactivateBulkMutation.mutate(selectedIds)} disabled={deactivateBulkMutation.isPending} className="bg-red-600 text-white">
              {deactivateBulkMutation.isPending ? "Deactivating..." : "Deactivate Selected"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
