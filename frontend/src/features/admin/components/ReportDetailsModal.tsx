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
  ExternalLink, 
  Map as MapIcon, 
  CheckCircle, 
  XCircle, 
  Loader2,
  Shield,
  Layers,
  FileText
} from "lucide-react";
import { FloodReport } from "../adminApi";
import { Button } from "@/shared/ui/Button";

interface ReportDetailsModalProps {
  report: FloodReport | null;
  isOpen: boolean;
  onClose: () => void;
  onViewOnMap: (report: FloodReport) => void;
  onApprove?: (reportId: number) => void;
  onReject?: (reportId: number) => void;
  isApproveLoading?: boolean;
  isRejectLoading?: boolean;
  onOpenImage?: (url: string) => void;
}

export const ReportDetailsModal: React.FC<ReportDetailsModalProps> = ({
  report,
  isOpen,
  onClose,
  onViewOnMap,
  onApprove,
  onReject,
  isApproveLoading = false,
  isRejectLoading = false,
  onOpenImage,
}) => {
  if (!isOpen || !report) return null;

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case "low":
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-lime-100 text-lime-800 border border-lime-200 uppercase">Passable (Low)</span>;
      case "medium":
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-yellow-100 text-yellow-800 border border-yellow-200 uppercase">Warning (Medium)</span>;
      case "high":
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-orange-100 text-orange-800 border border-orange-200 uppercase">Hazardous (High)</span>;
      case "extreme":
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-200 uppercase animate-pulse">Impassable (Extreme)</span>;
      default:
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-gray-100 text-gray-800 uppercase">Unknown</span>;
    }
  };

  const getStatusBadge = (stat: string) => {
    switch (stat) {
      case "pending":
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-200 uppercase">Pending</span>;
      case "approved":
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 uppercase">Approved</span>;
      case "rejected":
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200 uppercase">Rejected</span>;
      default:
        return null;
    }
  };

  const formatCoordinates = () => {
    if (!report.geometry) return "No coordinates mapped";
    if (report.geometry.type === "Point") {
      const [lng, lat] = report.geometry.coordinates;
      return `${lat.toFixed(5)}° N, ${lng.toFixed(5)}° E (Point)`;
    }
    const coords = report.geometry.coordinates;
    const mid = coords[Math.floor(coords.length / 2)];
    return `~${mid[1].toFixed(5)}° N, ${mid[0].toFixed(5)}° E (${coords.length} vertices Road Line)`;
  };

  const isOfficialReporter =
    report.reporter_role &&
    (report.reporter_role.includes("Admin") ||
      report.reporter_role.includes("DRRM") ||
      report.reporter_role.includes("Moderator") ||
      report.reporter_role.includes("Officer"));

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xs animate-fade-in">
      <div 
        className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/80">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-sm shadow-sm">
              #{report.id}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900">Flood Report Details</h3>
                {getStatusBadge(report.status)}
              </div>
              <p className="text-xs text-slate-500 flex items-center gap-1.5 mt-0.5">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                {format(new Date(report.created_at), "MMMM d, yyyy • h:mm a")}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 rounded-xl transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content Body */}
        <div className="p-6 overflow-y-auto space-y-5">
          {/* Severity & Ingestion Source Banner */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200/80">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Severity:</span>
              {getSeverityBadge(report.severity)}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Source:</span>
              <span className="px-2.5 py-0.5 rounded-md text-xs font-bold uppercase bg-slate-200/80 text-slate-700">
                {report.source}
              </span>
            </div>
          </div>

          {/* Raw Report Quote */}
          <div className="space-y-1.5">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-slate-500" />
              Verbatim Submission
            </div>
            <div className="p-4 bg-blue-50/50 border border-blue-100 rounded-xl text-sm font-medium text-slate-800 leading-relaxed italic">
              "{report.raw_text}"
            </div>
          </div>

          {/* Survey & Flood Metrics Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            {/* Water Height / Depth */}
            <div className="p-3.5 bg-slate-50/80 border border-slate-200/70 rounded-xl flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center shrink-0">
                <Ruler className="w-4 h-4" />
              </div>
              <div className="flex flex-col">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Water Level</span>
                <span className="text-sm font-bold text-slate-900">
                  {report.depth ? report.depth.replace(/_/g, ' ') : "Not specified"}
                </span>
              </div>
            </div>

            {/* Hidden Hazards */}
            <div className="p-3.5 bg-slate-50/80 border border-slate-200/70 rounded-xl flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-600 flex items-center justify-center shrink-0">
                <EyeOff className="w-4 h-4" />
              </div>
              <div className="flex flex-col">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Submerged Hazards</span>
                <span className="text-sm font-bold text-slate-900 capitalize">
                  {report.survey?.hidden_hazards || "Unsure / None reported"}
                </span>
              </div>
            </div>

            {/* Passable Vehicles */}
            <div className="p-3.5 bg-slate-50/80 border border-slate-200/70 rounded-xl flex items-start gap-3 sm:col-span-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-600 flex items-center justify-center shrink-0">
                <Car className="w-4 h-4" />
              </div>
              <div className="flex flex-col">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Passable Vehicles</span>
                <span className="text-sm font-bold text-slate-900">
                  {report.survey?.passable_vehicles 
                    ? report.survey.passable_vehicles.replace(/_/g, ' ') 
                    : "Standard passenger vehicles"}
                </span>
              </div>
            </div>
          </div>

          {/* Location & Spatial Metadata */}
          <div className="p-4 bg-slate-50/80 border border-slate-200/70 rounded-xl space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-400 uppercase tracking-wider">
                <MapPin className="w-3.5 h-3.5 text-slate-500" />
                Spatial Location
              </div>
              {report.zone_id && (
                <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-700 text-[10px] font-bold">
                  Linked to Zone #{report.zone_id}
                </span>
              )}
            </div>

            <div className="space-y-1">
              <div className="text-sm font-bold text-slate-900">
                {report.barangay ? `Brgy. ${report.barangay}, Pasig City` : "Pasig City, Metro Manila"}
              </div>
              {report.human_readable_location && (
                <div className="text-xs text-slate-600">
                  Landmark: {report.human_readable_location}
                </div>
              )}
              <div className="text-xs font-mono text-slate-500 bg-white p-2 rounded-lg border border-slate-200 inline-block">
                {formatCoordinates()}
              </div>
            </div>
          </div>

          {/* Reporter & Identity Profile */}
          <div className="p-4 bg-slate-50/80 border border-slate-200/70 rounded-xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${
                isOfficialReporter 
                  ? "bg-blue-600 text-white" 
                  : "bg-slate-200 text-slate-700"
              }`}>
                {isOfficialReporter ? <ShieldCheck className="w-5 h-5" /> : <User className="w-5 h-5" />}
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-slate-900">
                    {report.reporter_name || "System Ingestion"}
                  </span>
                  {report.reporter_role && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-blue-100 text-blue-700 border border-blue-200">
                      {report.reporter_role}
                    </span>
                  )}
                </div>
                <span className="text-xs text-slate-500">
                  {report.reporter_username ? `@${report.reporter_username}` : "Verified Citizen Contributor"}
                </span>
              </div>
            </div>

            {report.reporter_trust_score !== undefined && report.reporter_trust_score !== null && (
              <div className="flex flex-col items-end">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Trust Score</span>
                <span className="text-sm font-extrabold text-blue-600 flex items-center gap-1">
                  <Shield className="w-3.5 h-3.5 text-blue-500" />
                  {report.reporter_trust_score}%
                </span>
              </div>
            )}
          </div>

          {/* Attached Evidence Media */}
          {report.image_url && (
            <div className="space-y-2">
              <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Attached Flood Evidence</div>
              <div 
                onClick={() => onOpenImage && onOpenImage(report.image_url!)}
                className="relative rounded-xl overflow-hidden border border-slate-200 cursor-pointer group bg-slate-950/5 max-h-64 flex items-center justify-center"
              >
                <img 
                  src={report.image_url} 
                  alt="Flood report evidence" 
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 max-h-64"
                />
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-xs font-semibold gap-1.5 backdrop-blur-xs">
                  <ExternalLink className="w-4 h-4" />
                  Click for Fullscreen High-Res
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Modal Action Footer */}
        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50/80 flex flex-col sm:flex-row items-center justify-between gap-3">
          <Button
            onClick={() => {
              onClose();
              onViewOnMap(report);
            }}
            variant="outline"
            className="w-full sm:w-auto flex items-center justify-center gap-2 text-blue-600 border-blue-200 hover:bg-blue-50 text-sm font-semibold"
          >
            <MapIcon className="w-4 h-4 text-blue-600" />
            View on Map (Focus)
          </Button>

          {report.status === "pending" && onApprove && onReject && (
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Button
                onClick={() => onReject(report.id)}
                disabled={isRejectLoading}
                variant="outline"
                className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 text-rose-600 border-rose-200 hover:bg-rose-50 text-sm font-semibold"
              >
                {isRejectLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                Reject
              </Button>
              <Button
                onClick={() => onApprove(report.id)}
                disabled={isApproveLoading}
                className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold"
              >
                {isApproveLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                Approve
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
