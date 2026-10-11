"use client";

import { useId, useRef } from "react";
import { Camera, CheckCircle, ImagePlus, X, FileVideo } from "lucide-react";
import { Button } from "@/shared/ui";
import { cn } from "@/lib/utils";
import { FLOOD_DEPTH_OPTIONS } from "@/lib/floodDepth";
import { HAZARD_OPTIONS, VEHICLE_OPTIONS } from "./floodSurvey";
import type { useFloodMedia } from "./useFloodMedia";

export const floodDepthColors = {
  low: ["border-lime-300 text-lime-700 bg-lime-50 hover:bg-lime-100", "border-lime-400 bg-lime-100 text-lime-800 ring-2 ring-lime-300/50", "bg-[#d8ed34]"],
  medium: ["border-amber-300 text-amber-700 bg-amber-50 hover:bg-amber-100", "border-amber-400 bg-amber-100 text-amber-800 ring-2 ring-amber-300/50", "bg-amber-400"],
  high: ["border-orange-300 text-orange-700 bg-orange-50 hover:bg-orange-100", "border-orange-400 bg-orange-100 text-orange-800 ring-2 ring-orange-300/50", "bg-orange-500"],
  extreme: ["border-red-300 text-red-700 bg-red-50 hover:bg-red-100", "border-red-400 bg-red-100 text-red-800 ring-2 ring-red-300/50", "bg-red-600"],
};

export function FloodDepthField({ value, onChange }: { value: string | null; onChange: (value: string | null) => void }) {
  return <fieldset className="space-y-1" aria-label="Flood Severity">
    <legend className="mb-1.5 text-sm font-semibold text-gray-800">Flood Severity <span className="ml-0.5 text-red-500">*</span></legend>
    <p className="mb-2 text-[11px] text-gray-500">Half-Tire to Knee water is not passable to light vehicles; Tires and deeper are blocked for normal navigation.</p>
    <div className="grid grid-cols-4 gap-1.5 sm:gap-2">{FLOOD_DEPTH_OPTIONS.map(option => <button type="button" key={option.id} aria-pressed={value === option.id} onClick={() => onChange(value === option.id ? null : option.id)} className={cn("flex flex-col items-center text-center gap-0.5 rounded-lg border px-1 py-1.5 sm:px-2 sm:py-2 text-xs font-semibold transition-all leading-tight", floodDepthColors[option.severity][value === option.id ? 1 : 0])}>
      <span className={cn("w-3.5 h-3.5 rounded-sm mb-0.5 shadow-sm shadow-black/10 shrink-0", floodDepthColors[option.severity][2])} /><span className="truncate max-w-full">{option.label}</span><span className="font-normal text-[10px] opacity-75 whitespace-nowrap">{option.formatted}</span>
    </button>)}</div>

  </fieldset>;
}

export function FloodMediaField({ media, capture = false }: { media: ReturnType<typeof useFloodMedia>; capture?: boolean }) {
  const camera = useRef<HTMLInputElement>(null);
  const { mediaFiles, setMediaFiles, getImagePreviewUrl, removeMediaFile } = media;
  const add = (input: HTMLInputElement) => { const files = Array.from(input.files ?? []); setMediaFiles(previous => [...previous, ...files]); input.value = ""; };
  return <div className="space-y-1.5">
    <p className="mb-1.5 text-sm font-semibold text-gray-800">Photos &amp; Videos <span className="ml-1 font-normal text-gray-400">(Optional)</span></p>
    {capture && <><p className="text-xs text-gray-500">Up to 5 files, 10MB each. JPEG, PNG, GIF, WebP, MP4, MOV or WebM.</p><div className="flex flex-wrap gap-2 py-2">
      <Button type="button" variant="outline" size="sm" className="min-h-11 gap-1" onClick={() => camera.current?.click()}><Camera className="size-4" />Open camera</Button>
      <input ref={camera} aria-label="Capture flood photo or video" type="file" accept="image/*,video/*" capture="environment" className="hidden" onChange={event => add(event.currentTarget)} />
    </div></>}
    {mediaFiles.length > 0 && <div className="mb-2 space-y-2" aria-live="polite"><p className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-700"><CheckCircle className="size-3.5" />{mediaFiles.length} {mediaFiles.length === 1 ? "file" : "files"} {capture ? "ready to submit" : "ready to publish"}</p><div className="grid gap-2 sm:grid-cols-2">{mediaFiles.map((file, index) => {
      const preview = getImagePreviewUrl(file);
      return <div key={`${file.name}-${file.lastModified}-${index}`} className="flex min-w-0 items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 p-2">{preview ? <img src={preview} alt={`Selected ${file.name}`} className="size-11 shrink-0 rounded-md object-cover ring-1 ring-gray-200" /> : <div className="flex size-11 shrink-0 items-center justify-center rounded-md bg-orange-100 text-orange-700"><FileVideo className="size-5" /></div>}<div className="min-w-0 flex-1"><p className="truncate text-xs font-medium text-gray-700" title={file.name}>{file.name}</p><p className="text-[10px] text-gray-500">{file.type.startsWith("video/") ? "Video" : "Image"} · {file.size < 1048576 ? `${Math.max(1, Math.round(file.size / 1024))} KB` : `${(file.size / 1048576).toFixed(1)} MB`}</p></div><button type="button" aria-label={`Remove ${file.name}`} onClick={() => removeMediaFile(index)} className="shrink-0 rounded-full p-1 text-gray-500 hover:bg-gray-200 hover:text-gray-700"><X className="size-3.5" /></button></div>;
    })}</div></div>}
    <div className="relative flex w-full cursor-pointer select-none items-center justify-center rounded-md border border-dashed border-gray-300 bg-gray-50 px-3 py-4 text-sm text-gray-500 transition-colors hover:border-orange-300 hover:bg-orange-50 focus-within:ring-2 focus-within:ring-orange-400"><div className="flex flex-col items-center gap-1"><ImagePlus className="mb-1 size-5 text-gray-400" /><span className="font-medium text-gray-600">Add photos or videos</span><span className="text-[10px] text-gray-400">Select from your device</span></div><input type="file" multiple accept={capture ? "image/jpeg,image/png,image/gif,image/webp,video/mp4,video/quicktime,video/webm" : "image/*,video/*"} aria-label={capture ? "Attach flood zone photos or videos" : "Add photos or videos to flood report"} className="absolute inset-0 z-10 h-full w-full cursor-pointer opacity-0" onChange={event => add(event.currentTarget)} /></div>
  </div>;
}

export function FloodDescriptionField({ value, onChange, placeholder, required = false }: { value: string; onChange: (value: string) => void; placeholder: string; required?: boolean }) {
  const id = useId();
  return <div className="space-y-1.5"><label htmlFor={id} className="mb-1.5 block text-sm font-semibold text-gray-800">Description <span className="text-red-500">*</span></label><textarea id={id} aria-label="Description" placeholder={placeholder} value={value} onChange={event => onChange(event.target.value)} required={required} maxLength={required ? 3000 : undefined} rows={3} className="w-full resize-none rounded-md border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:border-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-400/30" /></div>;
}

export function FloodSurveyLauncher({ complete, onOpen, optional = false }: { complete: boolean; onOpen: () => void; optional?: boolean }) {
  return <div className="py-2 border-b border-gray-100 flex items-center justify-between"><div className="flex flex-col"><span className="text-sm font-semibold text-gray-800 flex items-center gap-1.5">Community Survey {optional ? <span className="text-xs font-normal text-gray-400">(Optional)</span> : <span className="text-red-500">*</span>}{complete && <CheckCircle className="size-3.5 text-green-500" />}</span><span className="text-[11px] text-gray-500">{complete ? "Survey complete. Thank you!" : optional ? "Add vehicle and hazard information" : "Required to submit report"}</span></div><Button type="button" variant="ghost" size="sm" onClick={onOpen} className="text-xs font-medium text-orange-600 bg-orange-50 hover:bg-orange-100 rounded-full">Take Survey</Button></div>;
}

export function FloodSurveyFields({ vehicles, onVehiclesChange, hazards, onHazardsChange, canonicalValues = false }: { vehicles: string[] | null; onVehiclesChange: (value: string[] | null) => void; hazards: string | null; onHazardsChange: (value: "yes" | "no" | "unsure") => void; canonicalValues?: boolean }) {
  return <div className="space-y-6"><fieldset className="space-y-2"><legend className="text-sm font-semibold text-gray-800">Which vehicles can safely pass?<span className="text-red-500"> *</span></legend><p className="text-xs text-gray-500">Select all that apply.</p><div className="grid grid-cols-2 gap-2">{VEHICLE_OPTIONS.map(option => {
    const value = canonicalValues ? option.id : option.label, checked = vehicles?.includes(value) ?? false;
    return <label key={option.id} className={cn("flex cursor-pointer items-center gap-2 rounded-lg border p-2 transition-colors", checked ? "border-orange-400 bg-orange-50" : "border-gray-200 hover:bg-gray-50")}><input type="checkbox" checked={checked} onChange={event => onVehiclesChange(event.target.checked ? [...vehicles ?? [], value] : (vehicles ?? []).filter(item => item !== value))} className="size-4 rounded border-gray-300 text-orange-600 focus:ring-2 focus:ring-orange-600" /><span className={cn("text-xs font-medium", checked ? "text-orange-900" : "text-gray-700")}>{option.label}</span></label>;
  })}</div></fieldset><fieldset className="space-y-2"><legend className="text-sm font-semibold text-gray-800">Are there hidden hazards?<span className="text-red-500"> *</span></legend><p className="text-xs text-gray-500">E.g., open manholes, large debris underwater.</p><div className="grid grid-cols-3 gap-2">{HAZARD_OPTIONS.map(option => <Button type="button" variant="outline" key={option.value} aria-pressed={hazards === option.value} onClick={() => onHazardsChange(option.value as "yes" | "no" | "unsure")} className={cn("min-h-11", hazards === option.value && option.activeClass)}>{option.label}</Button>)}</div></fieldset></div>;
}
