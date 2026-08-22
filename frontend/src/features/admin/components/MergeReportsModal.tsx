"use client";

/**
 * MergeReportsModal
 *
 * A multi-step modal that gives admins three paths when approving a flood report:
 *
 *   STEP 0 — Choose Action:
 *     A) Create New Zone   → go to STEP 1 (geometry editor)
 *     B) Merge into Zone   → go to STEP 2 (pick nearby zone)
 *     C) Batch Street Merge→ go to STEP 3 (confirm batch)
 *
 *   STEP 1 — (Optional) custom geometry confirmation
 *   STEP 2 — Pick which nearby zone to merge into
 *   STEP 3 — Confirm batch merge of all pending reports on the same street
 */

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus, Merge, Layers, ChevronLeft, Check, Loader2,
  AlertTriangle, MapPin, Clock, ArrowRight, Shield,
} from "lucide-react";
import { Button } from "@/shared/ui/Button";
import { Modal } from "@/shared/ui/Modal";
import type { FloodReport, NearbyZone, DrawnGeometry } from "@/features/admin/adminApi";

// ─── Types ────────────────────────────────────────────────────────────────────

type ModalStep = "choose" | "create_new" | "merge_zone" | "batch_street";

interface MergeReportsModalProps {
  isOpen: boolean;
  onClose: () => void;

  // The report being acted upon
  report: FloodReport | null;

  // Nearby zones detected by spatial query
  nearbyZones: NearbyZone[];
  nearbyLoading: boolean;

  // Batch candidates (other pending reports on same street)
  batchCandidates: FloodReport[];

  // Custom geometry drawn by the admin (if any)
  drawnGeometry: DrawnGeometry | null;
  onRequestDraw: () => void; // opens the map geometry editor

  // Submission handlers
  onApproveNew: (reportId: number, geometry?: DrawnGeometry) => void;
  onMergeInto: (reportId: number, targetZoneId: number) => void;
  onBatchMerge: (reportIds: number[], targetZoneId?: number) => void;

  isSubmitting: boolean;
}

// ─── Step Slide Variants ──────────────────────────────────────────────────────

const slideVariants = {
  enter: (dir: number) => ({ x: dir > 0 ? 60 : -60, opacity: 0 }),
  center: { x: 0, opacity: 1 },
  exit: (dir: number) => ({ x: dir > 0 ? -60 : 60, opacity: 0 }),
};

// ─── Component ────────────────────────────────────────────────────────────────

export function MergeReportsModal({
  isOpen,
  onClose,
  report,
  nearbyZones,
  nearbyLoading,
  batchCandidates,
  drawnGeometry,
  onRequestDraw,
  onApproveNew,
  onMergeInto,
  onBatchMerge,
  isSubmitting,
}: MergeReportsModalProps) {
  const [step, setStep] = useState<ModalStep>("choose");
  const [direction, setDirection] = useState(1);
  const [selectedZoneId, setSelectedZoneId] = useState<number | null>(null);

  const go = (nextStep: ModalStep) => {
    setDirection(1);
    setStep(nextStep);
  };

  const back = () => {
    setDirection(-1);
    setStep("choose");
  };

  const handleClose = () => {
    setStep("choose");
    setDirection(1);
    setSelectedZoneId(null);
    onClose();
  };

  if (!report) return null;

  const hasNearby = nearbyZones.length > 0;
  const hasBatch = batchCandidates.length > 0;

  // ── Step 0: Choose Action ──────────────────────────────────────────────────

  const StepChoose = (
    <div className="space-y-3">
      <p className="text-sm text-slate-600">
        How would you like to process{" "}
        <span className="font-bold text-slate-800">Report #{report.id}</span>?
      </p>

      {/* Option A: Create New */}
      <button
        onClick={() => go("create_new")}
        className="w-full text-left p-4 rounded-2xl border-2 border-slate-200 hover:border-blue-400 hover:bg-blue-50/40 transition-all group"
      >
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-xl bg-blue-100 flex items-center justify-center shrink-0 group-hover:bg-blue-200 transition-colors">
            <Plus className="w-4 h-4 text-blue-600" />
          </div>
          <div>
            <p className="text-sm font-bold text-slate-800">Create New Zone</p>
            <p className="text-xs text-slate-500 mt-0.5">
              Approve as an independent flood avoidance zone. Optionally draw a custom boundary.
            </p>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-blue-400 mt-2.5 ml-auto shrink-0 transition-colors" />
        </div>
      </button>

      {/* Option B: Merge into Nearby Zone */}
      <button
        onClick={() => go("merge_zone")}
        disabled={!hasNearby}
        className={`w-full text-left p-4 rounded-2xl border-2 transition-all group ${
          hasNearby
            ? "border-slate-200 hover:border-amber-400 hover:bg-amber-50/40 cursor-pointer"
            : "border-dashed border-slate-200 opacity-50 cursor-not-allowed"
        }`}
      >
        <div className="flex items-start gap-3">
          <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-colors ${
            hasNearby ? "bg-amber-100 group-hover:bg-amber-200" : "bg-slate-100"
          }`}>
            <Merge className={`w-4 h-4 ${hasNearby ? "text-amber-600" : "text-slate-400"}`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <p className="text-sm font-bold text-slate-800">Merge into Existing Zone</p>
              {hasNearby && (
                <span className="px-1.5 py-0.5 rounded-md bg-amber-100 text-amber-700 text-[10px] font-bold">
                  {nearbyZones.length} nearby
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {hasNearby
                ? `${nearbyZones.length} active zone${nearbyZones.length > 1 ? "s" : ""} detected within 500m. Both reporters get Trust Score credit.`
                : "No active zones detected within 500m of this report."}
            </p>
          </div>
          {hasNearby && (
            <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-amber-400 mt-2.5 ml-auto shrink-0 transition-colors" />
          )}
        </div>
      </button>

      {/* Option C: Batch Street Merge */}
      <button
        onClick={() => go("batch_street")}
        disabled={!hasBatch}
        className={`w-full text-left p-4 rounded-2xl border-2 transition-all group ${
          hasBatch
            ? "border-slate-200 hover:border-emerald-400 hover:bg-emerald-50/40 cursor-pointer"
            : "border-dashed border-slate-200 opacity-50 cursor-not-allowed"
        }`}
      >
        <div className="flex items-start gap-3">
          <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 transition-colors ${
            hasBatch ? "bg-emerald-100 group-hover:bg-emerald-200" : "bg-slate-100"
          }`}>
            <Layers className={`w-4 h-4 ${hasBatch ? "text-emerald-600" : "text-slate-400"}`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <p className="text-sm font-bold text-slate-800">Batch Merge Street Reports</p>
              {hasBatch && (
                <span className="px-1.5 py-0.5 rounded-md bg-emerald-100 text-emerald-700 text-[10px] font-bold">
                  {batchCandidates.length + 1} reports
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {hasBatch
                ? `Resolve ${batchCandidates.length} other pending report${batchCandidates.length > 1 ? "s" : ""} on the same street in one click.`
                : "No other pending reports detected on this street segment."}
            </p>
          </div>
          {hasBatch && (
            <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-emerald-400 mt-2.5 ml-auto shrink-0 transition-colors" />
          )}
        </div>
      </button>
    </div>
  );

  // ── Step 1: Create New Zone ─────────────────────────────────────────────────

  const StepCreateNew = (
    <div className="space-y-4">
      <div className="p-3 rounded-xl bg-blue-50 border border-blue-100 text-xs text-blue-800 flex items-start gap-2">
        <Plus className="w-4 h-4 shrink-0 mt-0.5 text-blue-600" />
        <p>
          Approving Report <strong>#{report.id}</strong> will create a new active flood avoidance
          zone. The reporter will receive{" "}
          <strong className="text-blue-700">+5 Trust Score</strong>.
        </p>
      </div>

      {/* Custom Geometry Section */}
      <div className="rounded-xl border border-slate-200 overflow-hidden">
        <div className="px-4 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
          <span className="text-xs font-bold text-slate-700">Zone Boundary</span>
          {drawnGeometry ? (
            <span className="text-[10px] font-bold px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full">
              Custom shape drawn ✓
            </span>
          ) : (
            <span className="text-[10px] text-slate-400">Auto-generated from report geometry</span>
          )}
        </div>
        <div className="p-4">
          {drawnGeometry ? (
            <div className="flex items-center gap-2 text-xs text-emerald-700">
              <Check className="w-4 h-4 text-emerald-500" />
              <span>
                Custom <strong>{drawnGeometry.type}</strong> boundary will be used (
                {drawnGeometry.type === "Polygon"
                  ? `${drawnGeometry.coordinates[0].length - 1} vertices`
                  : `${drawnGeometry.coordinates.length} points`}
                )
              </span>
            </div>
          ) : (
            <p className="text-xs text-slate-500 mb-3">
              The system will auto-buffer the report&apos;s{" "}
              <strong>{report.geometry?.type || "location"}</strong> geometry into a flood zone
              polygon. Or you can draw a custom boundary on the map.
            </p>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={onRequestDraw}
            className="mt-3 h-8 text-xs px-3 rounded-xl w-full border-dashed"
          >
            {drawnGeometry ? "✏️ Redraw Boundary on Map" : "✏️ Draw Custom Boundary on Map"}
          </Button>
        </div>
      </div>

      {/* Report Info Summary */}
      <div className="text-xs text-slate-500 flex flex-col gap-1 px-1">
        <div className="flex items-center gap-2">
          <MapPin className="w-3.5 h-3.5 text-slate-400" />
          <span>{report.barangay ? `Brgy. ${report.barangay}, Pasig` : "Pasig City"}</span>
        </div>
        <div className="flex items-center gap-2">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>Reported {new Date(report.created_at).toLocaleString()}</span>
        </div>
      </div>

      <div className="flex gap-2 pt-1 border-t border-slate-100">
        <Button variant="outline" size="sm" onClick={back} className="h-9 rounded-xl flex-1">
          <ChevronLeft className="w-3.5 h-3.5 mr-1" /> Back
        </Button>
        <Button
          variant="primary"
          size="sm"
          disabled={isSubmitting}
          onClick={() => onApproveNew(report.id, drawnGeometry ?? undefined)}
          className="h-9 rounded-xl flex-1 gap-1.5 shadow-sm"
        >
          {isSubmitting ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Check className="w-3.5 h-3.5" />
          )}
          {isSubmitting ? "Creating..." : "Create Zone"}
        </Button>
      </div>
    </div>
  );

  // ── Step 2: Merge into Nearby Zone ─────────────────────────────────────────

  const StepMergeZone = (
    <div className="space-y-4">
      <div className="p-3 rounded-xl bg-amber-50 border border-amber-100 text-xs text-amber-800 flex items-start gap-2">
        <Merge className="w-4 h-4 shrink-0 mt-0.5 text-amber-600" />
        <p>
          Merging will link Report <strong>#{report.id}</strong> into the selected zone. No
          duplicate routing barrier will be created. Both reporters get{" "}
          <strong className="text-amber-700">+5 Trust Score</strong>.
        </p>
      </div>

      <p className="text-xs font-semibold text-slate-600 px-1">Select target zone:</p>

      {nearbyLoading ? (
        <div className="flex items-center justify-center py-6 gap-2 text-slate-400">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-xs">Loading nearby zones...</span>
        </div>
      ) : (
        <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
          {nearbyZones.map((zone) => (
            <button
              key={zone.id}
              onClick={() => setSelectedZoneId(zone.id)}
              className={`w-full text-left p-3 rounded-xl border-2 transition-all ${
                selectedZoneId === zone.id
                  ? "border-amber-400 bg-amber-50"
                  : "border-slate-200 hover:border-amber-300 hover:bg-amber-50/30"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <Shield className="w-3.5 h-3.5 text-emerald-500" />
                  <span className="text-xs font-bold text-slate-800">Zone #{zone.id}</span>
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-extrabold uppercase border ${
                    zone.severity?.toLowerCase() === "low"
                      ? "bg-lime-100 text-lime-800 border-lime-300"
                      : zone.severity?.toLowerCase() === "medium"
                      ? "bg-amber-100 text-amber-800 border-amber-300"
                      : zone.severity?.toLowerCase() === "high"
                      ? "bg-orange-100 text-orange-800 border-orange-300"
                      : "bg-red-100 text-red-700 border-red-300"
                  }`}>
                    {zone.severity}
                  </span>
                </div>
                <span className="text-[10px] font-semibold text-slate-500">
                  {Math.round(zone.distance_meters)}m away
                </span>
              </div>
              <div className="text-[10px] text-slate-400">
                {zone.report_count} report{zone.report_count !== 1 ? "s" : ""} linked ·{" "}
                {new Date(zone.created_at).toLocaleDateString()}
              </div>
            </button>
          ))}
        </div>
      )}

      <div className="flex gap-2 pt-1 border-t border-slate-100">
        <Button variant="outline" size="sm" onClick={back} className="h-9 rounded-xl flex-1">
          <ChevronLeft className="w-3.5 h-3.5 mr-1" /> Back
        </Button>
        <Button
          variant="primary"
          size="sm"
          disabled={!selectedZoneId || isSubmitting}
          onClick={() => selectedZoneId && onMergeInto(report.id, selectedZoneId)}
          className="h-9 rounded-xl flex-1 gap-1.5 shadow-sm"
        >
          {isSubmitting ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Merge className="w-3.5 h-3.5" />
          )}
          {isSubmitting ? "Merging..." : "Merge into Zone"}
        </Button>
      </div>
    </div>
  );

  // ── Step 3: Batch Street Merge ──────────────────────────────────────────────

  const StepBatchStreet = (
    <div className="space-y-4">
      <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-100 text-xs text-emerald-800 flex items-start gap-2">
        <Layers className="w-4 h-4 shrink-0 mt-0.5 text-emerald-600" />
        <p>
          This will resolve <strong>{batchCandidates.length + 1} reports</strong> (including this
          one) in a single action by creating one shared zone. All reporters receive Trust Score
          credit.
        </p>
      </div>

      <p className="text-xs font-semibold text-slate-600 px-1">Reports to be batch-merged:</p>
      <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
        {/* Current report */}
        <div className="flex items-center gap-2 p-2.5 rounded-xl bg-blue-50 border border-blue-100">
          <div className="w-5 h-5 rounded-full bg-blue-600 text-white text-[9px] font-bold flex items-center justify-center shrink-0">
            ★
          </div>
          <div className="flex-1 min-w-0">
            <span className="text-xs font-bold text-slate-800">Report #{report.id}</span>
            <span className="ml-2 text-[10px] text-blue-600 font-medium">(this report)</span>
          </div>
          <span className={`px-1.5 py-0.5 rounded text-[9px] font-extrabold uppercase border ${
            report.severity?.toLowerCase() === "low"
              ? "bg-lime-100 text-lime-800 border-lime-300"
              : report.severity?.toLowerCase() === "medium"
              ? "bg-amber-100 text-amber-800 border-amber-300"
              : report.severity?.toLowerCase() === "high"
              ? "bg-orange-100 text-orange-800 border-orange-300"
              : "bg-red-100 text-red-700 border-red-300"
          }`}>
            {report.severity}
          </span>
        </div>
        {/* Other candidates */}
        {batchCandidates.map((r, i) => (
          <div key={r.id} className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-50 border border-slate-100">
            <div className="w-5 h-5 rounded-full bg-slate-200 text-slate-600 text-[9px] font-bold flex items-center justify-center shrink-0">
              {i + 2}
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-xs font-bold text-slate-800">Report #{r.id}</span>
            </div>
            <span className={`px-1.5 py-0.5 rounded text-[9px] font-extrabold uppercase border ${
              r.severity?.toLowerCase() === "low"
                ? "bg-lime-100 text-lime-800 border-lime-300"
                : r.severity?.toLowerCase() === "medium"
                ? "bg-amber-100 text-amber-800 border-amber-300"
                : r.severity?.toLowerCase() === "high"
                ? "bg-orange-100 text-orange-800 border-orange-300"
                : "bg-red-100 text-red-700 border-red-300"
            }`}>
              {r.severity}
            </span>
          </div>
        ))}
      </div>

      <div className="flex gap-2 pt-1 border-t border-slate-100">
        <Button variant="outline" size="sm" onClick={back} className="h-9 rounded-xl flex-1">
          <ChevronLeft className="w-3.5 h-3.5 mr-1" /> Back
        </Button>
        <Button
          variant="primary"
          size="sm"
          disabled={isSubmitting}
          onClick={() => onBatchMerge([report.id, ...batchCandidates.map((r) => r.id)])}
          className="h-9 rounded-xl flex-1 gap-1.5 bg-emerald-600 hover:bg-emerald-700 shadow-sm"
        >
          {isSubmitting ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Layers className="w-3.5 h-3.5" />
          )}
          {isSubmitting ? "Processing..." : `Batch Merge ${batchCandidates.length + 1} Reports`}
        </Button>
      </div>
    </div>
  );

  // ── Title per step ────────────────────────────────────────────────────────────

  const titles: Record<ModalStep, string> = {
    choose: `Approve Report #${report.id}`,
    create_new: "Create New Flood Zone",
    merge_zone: "Merge into Existing Zone",
    batch_street: "Batch Merge Street Reports",
  };

  const stepContent: Record<ModalStep, React.ReactNode> = {
    choose: StepChoose,
    create_new: StepCreateNew,
    merge_zone: StepMergeZone,
    batch_street: StepBatchStreet,
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title={titles[step]}>
      <AnimatePresence mode="wait" custom={direction}>
        <motion.div
          key={step}
          custom={direction}
          variants={slideVariants}
          initial="enter"
          animate="center"
          exit="exit"
          transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
        >
          {stepContent[step]}
        </motion.div>
      </AnimatePresence>
    </Modal>
  );
}
