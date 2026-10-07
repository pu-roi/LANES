"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowLeft, CheckCircle } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Button, LocationInputGroup } from "@/shared/ui";
import { useAuth } from "@/hooks/useAuth";
import { apiClient } from "@/lib/apiClient";
import { formatFloodDepth } from "@/lib/floodDepth";
import { useMapContext, type ActivePoint } from "@/features/map/MapContext";
import { getCurrentLocation } from "@/features/geocoding/geocodingApi";
import { FloodDepthField, FloodDescriptionField, FloodMediaField, FloodSurveyFields, FloodSurveyLauncher } from "./FloodReportFields";
import { useFloodMedia } from "./useFloodMedia";
import { useZoneRoadPreview } from "./useZoneRoadPreview";
import { ZONE_CONDITIONS, type ZoneCondition, type ZoneUpdateContext } from "./zoneUpdatesApi";

export function ZoneUpdateForm({ zone, initialCondition, onClose, onSubmittingChange }: { zone: ZoneUpdateContext; initialCondition: ZoneCondition; onClose: () => void; onSubmittingChange: (busy: boolean) => void }) {
  const { isAuthenticated } = useAuth();
  const { zoneUpdateRoad: road, setZoneUpdateRoad: setRoad, activePoint, setActivePoint, setIsPickingOnMap } = useMapContext();
  const [condition, setCondition] = useState(initialCondition);
  const [description, setDescription] = useState("");
  const [depth, setDepth] = useState(zone.depth ?? "");
  const [vehicles, setVehicles] = useState<string[] | null>(null);
  const [hazards, setHazards] = useState<"yes" | "no" | "unsure" | null>(null);
  const [startText, setStartText] = useState<string | null>(null), [endText, setEndText] = useState<string | null>(null);
  const [step, setStep] = useState<1 | 2>(1), [showSurvey, setShowSurvey] = useState(false);
  const [busy, setBusy] = useState(false), [sent, setSent] = useState(false), [error, setError] = useState("");
  const media = useFloodMedia();
  const request = useRef<{ signature: string; id: string } | null>(null);
  const initialized = useRef(false);
  const context = useQuery({ queryKey: ["zone-update-context", zone.id], enabled: isAuthenticated,
    queryFn: () => apiClient.get<{ start: [number, number] | null; end: [number, number] | null; name: string | null; is_bidirectional: boolean; has_multiple_segments?: boolean }>(`/zones/${zone.id}/update-context`), retry: false });
  useEffect(() => {
    if (!context.data || initialized.current) return;
    initialized.current = true;
    const data = context.data;
    let cancelled = false;
    queueMicrotask(() => { if (!cancelled) setRoad(previous => previous.start || previous.end ? previous : {
      start: data.start ? { coords: data.start, label: `${data.start[1].toFixed(5)}, ${data.start[0].toFixed(5)}` } : null,
      end: data.end ? { coords: data.end, label: `${data.end[1].toFixed(5)}, ${data.end[0].toFixed(5)}` } : null,
      isBidirectional: data.is_bidirectional,
    }); });
    return () => { cancelled = true; };
  }, [context.data, setRoad]);
  const preview = useZoneRoadPreview(road.start, road.end, road.isBidirectional, isAuthenticated);
  const point = (which: "start" | "end", coords: [number, number] | null, label = "") => {
    setRoad(previous => ({ ...previous, [which]: coords ? { coords, label } : null }));
    if (which === "start") setStartText(null); else setEndText(null);
  };
  const currentLocation = async (target: ActivePoint) => {
    try { const coords = await getCurrentLocation(); point(target === "zone_update_start" ? "start" : "end", coords, "Current Location"); setError(""); }
    catch (failure) { setError(failure instanceof Error ? failure.message : "Unable to retrieve your location. Choose on the map instead."); }
  };
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (step === 1) { setStep(2); return; }
    setError(""); setBusy(true); onSubmittingChange(true);
    try {
      const details = { condition, description, depth: condition === "no_floodwater" ? null : depth || null,
        road_start: road.start?.coords, road_end: road.end?.coords, start_label: road.start?.label, end_label: road.end?.label,
        is_bidirectional: road.isBidirectional, passable_vehicles: vehicles, hidden_hazards: hazards ?? "unsure" };
      const signature = JSON.stringify([details, media.mediaFiles.map(file => [file.name, file.size, file.lastModified])]);
      if (request.current?.signature !== signature) request.current = { signature, id: crypto.randomUUID() };
      const form = new FormData(); form.append("body", JSON.stringify({ ...details, request_id: request.current.id }));
      media.mediaFiles.forEach(file => form.append("media", file));
      await apiClient.post(`/zones/${zone.id}/updates`, form);
      setSent(true); media.clearMediaFiles();
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Your update could not be submitted. Please retry."); }
    finally { setBusy(false); onSubmittingChange(false); }
  };
  const surveyComplete = !!vehicles?.length && hazards !== null;
  const canContinue = !!road.start && !!road.end && (condition === "no_floodwater" || !!depth) && !preview.isFetching && !preview.isError;
  return <div className="space-y-4">
    <div className="text-sm"><p className="mb-1 text-xs font-semibold text-orange-700">Updating existing flood zone</p><p className="font-semibold text-gray-900">{zone.name || `Zone #${zone.id}`}</p><p className="mt-1 text-xs text-gray-500">Official depth: {formatFloodDepth(zone.depth)}</p></div>
    {sent ? <div role="status" className="space-y-3 py-4"><CheckCircle className="size-8 text-emerald-600" /><p className="font-semibold">Update received</p><p className="text-sm text-gray-600">Staff will review the reported conditions and proposed road extent.</p><Button onClick={onClose} className="min-h-11 w-full bg-orange-500 hover:bg-orange-600">Done</Button></div>
      : <form onSubmit={submit} className="relative flex flex-col space-y-4"><fieldset disabled={busy} className="space-y-4">
        {step === 1 && <>
          <fieldset><legend className="text-sm font-semibold text-gray-800">Flood status</legend><div className="mt-2 grid grid-cols-2 gap-2">{ZONE_CONDITIONS.map(item => <Button type="button" key={item.id} variant="outline" aria-pressed={condition === item.id} onClick={() => setCondition(item.id)} className={`min-h-11 whitespace-normal px-2 text-xs ${item.id === "other_change" ? "col-span-2" : ""} ${condition === item.id ? "border-orange-400 bg-orange-50 text-orange-700" : ""}`}>{item.label}</Button>)}</div></fieldset>
          {context.isPending && <p role="status" className="text-xs text-gray-500">Loading zone location...</p>}
          {context.isError && <p role="alert" className="text-xs text-red-700">Could not load the original road endpoints. <Button type="button" size="sm" variant="ghost" onClick={() => context.refetch()}>Retry</Button></p>}
          {context.data && !context.data.start && <p className="text-xs text-gray-500">This zone was drawn as an area. Select the start and end of the road you are reporting.</p>}
          {context.data?.has_multiple_segments && <p className="text-xs text-gray-500">This zone includes multiple road sections. Check the selected section before submitting.</p>}
          <LocationInputGroup startInput={startText ?? road.start?.label ?? ""} endInput={endText ?? road.end?.label ?? ""}
            setStartInput={value => { setStartText(value); setRoad(previous => ({ ...previous, start: null })); }} setEndInput={value => { setEndText(value); setRoad(previous => ({ ...previous, end: null })); }}
            activePoint={activePoint} setActivePoint={setActivePoint} startPointId="zone_update_start" endPointId="zone_update_end"
            onStartSelect={value => { point("start", [value.lng, value.lat], value.label); setActivePoint("zone_update_end"); setIsPickingOnMap(false); }} onEndSelect={value => { point("end", [value.lng, value.lat], value.label); setActivePoint(null); setIsPickingOnMap(false); }}
            onStartClear={() => point("start", null)} onEndClear={() => point("end", null)} canSwap={!!road.start && !!road.end}
            onSwap={() => { setRoad(previous => ({ ...previous, start: previous.end, end: previous.start })); setStartText(null); setEndText(null); }}
            onPickOnMap={target => { setStartText(null); setEndText(null); setActivePoint(target); setIsPickingOnMap(true); }} onUseCurrentLocation={currentLocation}
            startPlaceholder="e.g. Ortigas Ave, Pasig (Start)" endPlaceholder="e.g. C. Raymundo Ave (End)" />
          <label className="flex items-start gap-2 px-1 cursor-pointer"><input type="checkbox" checked={road.isBidirectional} onChange={event => setRoad(previous => ({ ...previous, isBidirectional: event.target.checked }))} className="mt-0.5 size-4 rounded border-gray-300 text-orange-600 focus:ring-orange-600" /><span className="text-[13px] font-semibold text-gray-800">Affects both sides of the road (2-way)<span className="block text-[11px] font-normal text-gray-500">Keep checked if the flood blocks traffic in both directions.</span></span></label>
          {preview.isFetching && <p role="status" className="text-xs text-gray-500">Verifying the selected road...</p>}
          {preview.isError && <p role="alert" className="text-xs text-red-700">Could not verify the selected road. <Button type="button" variant="ghost" size="sm" onClick={() => preview.refetch()}>Retry</Button></p>}
          {preview.data && <p className="text-[11px] text-gray-500">{preview.data.message}</p>}
          {condition !== "no_floodwater" ? <FloodDepthField value={depth || null} onChange={value => setDepth(value ?? "")} /> : <p className="text-xs text-gray-500">Report only the road section you can see. Evidence helps staff verify clearance.</p>}
        </>}
        {step === 2 && !showSurvey && <>
          <FloodSurveyLauncher complete={surveyComplete} onOpen={() => setShowSurvey(true)} optional />
          <FloodMediaField media={media} capture />
          <FloodDescriptionField value={description} onChange={setDescription} required placeholder="Describe the flood conditions and any changes to the affected road." />
        </>}
        {step === 2 && showSurvey && <div className="space-y-6"><div className="flex items-center gap-2 pb-2 border-b border-gray-100"><Button type="button" variant="ghost" size="sm" aria-label="Back to report" onClick={() => setShowSurvey(false)}><ArrowLeft className="size-4" /></Button><h3 className="text-sm font-bold text-gray-800">Community Survey</h3></div><FloodSurveyFields vehicles={vehicles} onVehiclesChange={setVehicles} hazards={hazards} onHazardsChange={setHazards} canonicalValues /></div>}
      </fieldset>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      <div className="sticky bottom-0 -mx-4 -mb-4 px-4 py-3 bg-white/95 backdrop-blur-md border-t border-gray-100 mt-auto z-30 shadow-[0_-4px_16px_rgba(0,0,0,0.04)] rounded-b-2xl">
        {showSurvey ? <Button type="button" onClick={() => setShowSurvey(false)} className="min-h-11 w-full bg-gray-900 hover:bg-gray-800">Done &amp; Return</Button> : step === 1 ? <Button type="submit" disabled={!canContinue} className="min-h-11 w-full bg-gray-900 hover:bg-gray-800">Next Step</Button> : <div className="flex gap-2"><Button type="button" variant="outline" disabled={busy} className="min-h-11" onClick={() => setStep(1)}>Back</Button><Button type="submit" disabled={busy || description.trim().length < 3} className="min-h-11 flex-1 bg-orange-500 hover:bg-orange-600">{busy ? "Submitting..." : "Submit update"}</Button></div>}
        {!showSurvey && step === 2 && <p className="mt-2 text-center text-[11px] text-gray-500">Sent privately to Spatial Operations staff.</p>}
      </div>
    </form>}
  </div>;
}
