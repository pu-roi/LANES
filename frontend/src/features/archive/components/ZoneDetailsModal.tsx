"use client";

import React from "react";
import { format } from "date-fns";
import { 
  X, 
  MapPin, 
  ShieldCheck, 
  User, 
  Ruler, 
  Car, 
  EyeOff, 
  Clock, 
  Calendar, 
  AlertTriangle,
  FileText,
  Layers,
  RotateCcw,
  Trash2,
  Loader2
} from "lucide-react";
import { AvoidanceZone } from "@/features/admin/adminApi";
import { Button, Modal } from "@/shared/ui";

interface ZoneDetailsModalProps {
  zone: AvoidanceZone | null;
  isOpen: boolean;
  onClose: () => void;
  onRestore?: (zone: AvoidanceZone) => void;
  onHardDelete?: (zone: AvoidanceZone) => void;
  isRestoring?: boolean;
}

export function ZoneDetailsModal({
  zone,
  isOpen,
  onClose,
  onRestore,
  onHardDelete,
  isRestoring = false,
}: ZoneDetailsModalProps) {
  if (!isOpen || !zone) return null;

  const getSeverityBadge = (sev: string) => {
    switch (sev?.toLowerCase()) {
      case "extreme":
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-200 uppercase">Impassable (Extreme)</span>;
      case "high":
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-orange-100 text-orange-800 border border-orange-200 uppercase">Hazardous (High)</span>;
      case "medium":
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200 uppercase">Warning (Medium)</span>;
      case "low":
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-lime-100 text-lime-800 border border-lime-200 uppercase">Passable (Low)</span>;
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Archived Avoidance Zone #${zone.id}`}>
      <div className="space-y-5 text-gray-800 max-h-[75vh] overflow-y-auto pr-1">
        {/* Header Summary */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 bg-slate-50 border border-slate-200 rounded-xl">
          <div>
            <h3 className="text-base font-bold text-gray-900">
              {zone.name || `Avoidance Zone #${zone.id}`}
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              Created: {format(new Date(zone.created_at), "MMM d, yyyy • h:mm a")}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {getSeverityBadge(zone.severity)}
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-600 border border-gray-200">
              Deactivated
            </span>
          </div>
        </div>

        {/* Hazard Attributes */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          {zone.depth && (
            <div className="p-3 bg-white border border-gray-200 rounded-xl flex items-center gap-3">
              <Ruler className="w-4 h-4 text-blue-500 shrink-0" />
              <div>
                <p className="text-xs text-gray-400 font-medium">Estimated Depth</p>
                <p className="font-semibold text-gray-800">{zone.depth}</p>
              </div>
            </div>
          )}
          {zone.passable_vehicles && (
            <div className="p-3 bg-white border border-gray-200 rounded-xl flex items-center gap-3">
              <Car className="w-4 h-4 text-emerald-500 shrink-0" />
              <div>
                <p className="text-xs text-gray-400 font-medium">Passable Vehicles</p>
                <p className="font-semibold text-gray-800">{zone.passable_vehicles}</p>
              </div>
            </div>
          )}
          {zone.hidden_hazards && (
            <div className="p-3 bg-white border border-gray-200 rounded-xl flex items-center gap-3 col-span-1 sm:col-span-2">
              <EyeOff className="w-4 h-4 text-amber-500 shrink-0" />
              <div>
                <p className="text-xs text-gray-400 font-medium">Hidden Hazards</p>
                <p className="font-semibold text-gray-800">{zone.hidden_hazards}</p>
              </div>
            </div>
          )}
        </div>

        {/* Admin Notes & Rationale */}
        {zone.admin_notes && (
          <div className="p-3.5 bg-amber-50/60 border border-amber-200/80 rounded-xl text-xs space-y-1">
            <span className="font-bold text-amber-900 uppercase tracking-wider">Admin Notes</span>
            <p className="text-amber-950 whitespace-pre-wrap">{zone.admin_notes}</p>
          </div>
        )}
        {zone.merge_rationale && (
          <div className="p-3.5 bg-purple-50/60 border border-purple-200/80 rounded-xl text-xs space-y-1">
            <span className="font-bold text-purple-900 uppercase tracking-wider">Merge Rationale</span>
            <p className="text-purple-950 whitespace-pre-wrap">{zone.merge_rationale}</p>
          </div>
        )}

        {/* Contributors List */}
        {zone.contributors && zone.contributors.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-blue-500" />
              Associated Reports ({zone.contributors.length})
            </h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {zone.contributors.map((c) => (
                <div key={c.report_id} className="p-2.5 bg-gray-50 border border-gray-200 rounded-lg text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-gray-800">Report #{c.report_id}</span>
                    <span className="text-[10px] text-gray-400">{format(new Date(c.created_at), "MMM d, yyyy")}</span>
                  </div>
                  <p className="text-gray-600 truncate">{c.raw_text || "No report text"}</p>
                  <div className="text-[11px] text-gray-500 flex items-center gap-2">
                    <span>By: {c.reporter_name}</span>
                    <span>• Trust: {c.reporter_trust_score}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100 gap-2">
          {onHardDelete && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onHardDelete(zone)}
              className="text-red-600 border-red-200 hover:bg-red-50 rounded-xl gap-1.5"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Delete Permanently
            </Button>
          )}
          <div className="flex items-center gap-2 ml-auto">
            <Button variant="outline" size="sm" onClick={onClose} className="rounded-xl">
              Close
            </Button>
            {onRestore && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => onRestore(zone)}
                disabled={isRestoring}
                className="rounded-xl gap-1.5 bg-blue-600 hover:bg-blue-700 text-white"
              >
                {isRestoring ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <RotateCcw className="w-3.5 h-3.5" />
                )}
                Restore & Reactivate Zone
              </Button>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
}
