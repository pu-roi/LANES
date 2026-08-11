"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";
import { Button } from "@/shared/ui/Button";
import { Loader2, CheckCircle, XCircle, MapPin, AlertTriangle } from "lucide-react";

interface PointGeometry {
  type: string;
  coordinates: [number, number];
}

interface FloodReport {
  id: number;
  source: string;
  raw_text: string;
  severity: string | null;
  geometry: PointGeometry | null;
  status: string;
  created_at: string;
}

export default function AdminDashboard() {
  const queryClient = useQueryClient();

  const { data: reports, isLoading, error } = useQuery<FloodReport[]>({
    queryKey: ["pendingReports"],
    queryFn: () => apiClient.get("/admin/reports/pending"),
  });

  const approveMutation = useMutation({
    mutationFn: (id: number) => apiClient.post(`/admin/reports/${id}/approve`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pendingReports"] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (id: number) => apiClient.post(`/admin/reports/${id}/reject`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pendingReports"] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-lg">
        Error loading reports: {error.message}
      </div>
    );
  }

  return (
    <div className="w-full max-w-[1600px] mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Pending Moderation</h1>
        <p className="text-gray-600 mt-1">Review and approve extracted flood reports to automatically generate avoidance zones.</p>
      </div>

      {!reports || reports.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center shadow-sm">
          <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">All caught up!</h3>
          <p className="text-gray-500 mt-1">There are no pending flood reports in the queue.</p>
        </div>
      ) : (
        <div className="grid gap-6">
          {reports.map((report) => (
            <div key={report.id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col md:flex-row">
              <div className="p-6 flex-1">
                <div className="flex items-center justify-between mb-4">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 uppercase tracking-wide">
                    {report.source}
                  </span>
                  <span className="text-sm text-gray-500">
                    {new Date(report.created_at).toLocaleString()}
                  </span>
                </div>
                
                <p className="text-gray-900 text-base mb-4">
                  "{report.raw_text}"
                </p>

                <div className="flex flex-wrap gap-4 mt-auto">
                  {report.severity && (
                    <div className="flex items-center text-sm font-medium text-amber-700 bg-amber-50 px-3 py-1 rounded-md">
                      Severity: {report.severity}
                    </div>
                  )}
                  {report.geometry ? (
                    <div className="flex items-center text-sm font-medium text-emerald-700 bg-emerald-50 px-3 py-1 rounded-md">
                      <MapPin className="w-4 h-4 mr-1.5" />
                      {report.geometry.coordinates[1].toFixed(4)}, {report.geometry.coordinates[0].toFixed(4)}
                    </div>
                  ) : (
                    <div className="flex items-center text-sm font-medium text-gray-500 bg-gray-50 px-3 py-1 rounded-md">
                      No coordinates extracted
                    </div>
                  )}
                </div>
              </div>

              <div className="bg-gray-50 border-t md:border-t-0 md:border-l border-gray-200 p-6 flex flex-row md:flex-col items-center justify-center gap-3 md:w-48">
                <Button 
                  onClick={() => approveMutation.mutate(report.id)}
                  disabled={approveMutation.isPending}
                  className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700"
                >
                  <CheckCircle className="w-4 h-4" />
                  Approve
                </Button>
                <Button 
                  onClick={() => rejectMutation.mutate(report.id)}
                  disabled={rejectMutation.isPending}
                  variant="outline"
                  className="w-full flex items-center justify-center gap-2 text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300"
                >
                  <XCircle className="w-4 h-4" />
                  Reject
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
