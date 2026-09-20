"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { AlertTriangle, CloudRain, EyeOff, MessageSquare, RefreshCw, ShieldCheck, XCircle } from "lucide-react";
import { apiClient } from "@/lib/apiClient";
import { Button, Card, CardContent, Skeleton, Tabs, useToast } from "@/shared/ui";
import { FloodModerationQueue } from "./components/FloodModerationQueue";

type Report = {
  id: number;
  post_id: number;
  post_content: string;
  reason: string;
  details?: string;
  created_at: string;
  open_report_count: number;
};

const reasonLabel: Record<string, string> = {
  spam_scam: "Spam or scam",
  misinformation: "Misinformation",
  harassment_hate: "Harassment or hate",
  explicit_violent: "Explicit or violent content",
  other: "Other",
};

export default function ModerationCenterPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [activeTab, setActiveTab] = useState<"community" | "flood">("community");
  const reports = useQuery({
    queryKey: ["moderation-reports"],
    queryFn: () => apiClient.get<Report[]>("/admin/moderation/reports"),
  });
  const resolve = useMutation({
    mutationFn: ({ postId, action }: { postId: number; action: "dismiss" | "warn" | "hide" }) =>
      apiClient.post(`/admin/moderation/posts/${postId}/resolve`, { action }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["moderation-reports"] });
      toast.success(
        "Reports resolved",
        variables.action === "hide"
          ? "The post has been hidden and moved to the Archive Center."
          : `The reports were ${variables.action}ed.`
      );
    },
    onError: (error: Error) => toast.error("Could not resolve reports", error.message),
  });

  return <div className="w-full max-w-[1600px] mx-auto space-y-6 text-gray-900 pb-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom))]">
    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Moderation Center</h1>
        <p className="text-gray-500 text-sm mt-1">Track Community and Flood Report cases. Flood decisions stay in Spatial Operations.</p>
      </div>
      <Button onClick={() => activeTab === "community" ? reports.refetch() : queryClient.invalidateQueries({ queryKey: ["flood-moderation-cases"] })} variant="outline" className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900">
        <RefreshCw className="w-4 h-4" />
        Refresh
      </Button>
    </div>

    <Tabs<"community" | "flood">
      tabs={[
        { id: "community", label: "Community Post Reports", icon: MessageSquare },
        { id: "flood", label: "Flood Report Moderation", icon: CloudRain },
      ]}
      activeTab={activeTab}
      onChange={setActiveTab}
      variant="underline"
      layoutId="moderation-center-tabs"
      className="w-full"
    />

    {activeTab === "community" && <>
    {reports.isLoading && (
      <Card className="shadow-sm">
        <CardContent className="space-y-3 py-5">
          <Skeleton className="h-5 w-1/4" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </CardContent>
      </Card>
    )}
    {reports.isError && (
      <Card className="border-red-200 bg-red-50 shadow-sm">
        <CardContent className="flex items-center gap-3 text-sm text-red-800">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          Could not load moderation reports. Please refresh and try again.
        </CardContent>
      </Card>
    )}
    {reports.data?.length === 0 && (
      <Card className="shadow-sm">
        <CardContent className="py-16 text-center text-sm text-gray-500">No open Community Post reports.</CardContent>
      </Card>
    )}
    {reports.data?.map((report) => (
      <Card key={report.id} className="shadow-sm">
        <CardContent className="p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="font-semibold text-gray-900">{reasonLabel[report.reason] || report.reason}</p>
              <p className="mt-1 text-xs text-gray-500">
                {report.open_report_count} open report{report.open_report_count === 1 ? "" : "s"} · Post #{report.post_id}
              </p>
            </div>
            <AlertTriangle className="h-5 w-5 text-amber-500" />
          </div>
          <p className="mt-4 whitespace-pre-wrap text-sm text-gray-700">{report.post_content}</p>
          {report.details && <p className="mt-3 text-sm text-gray-500">Reporter details: {report.details}</p>}
          <div className="mt-5 flex flex-wrap justify-end gap-2">
            <Button size="sm" variant="secondary" disabled={resolve.isPending} onClick={() => resolve.mutate({ postId: report.post_id, action: "dismiss" })}>
              <XCircle className="mr-1 h-4 w-4" />Dismiss
            </Button>
            <Button size="sm" variant="outline" disabled={resolve.isPending} onClick={() => resolve.mutate({ postId: report.post_id, action: "warn" })}>
              <ShieldCheck className="mr-1 h-4 w-4" />Warn
            </Button>
            <Button size="sm" variant="danger" disabled={resolve.isPending} onClick={() => resolve.mutate({ postId: report.post_id, action: "hide" })}>
              <EyeOff className="mr-1 h-4 w-4" />Hide
            </Button>
          </div>
        </CardContent>
      </Card>
    ))}
    </>}
    {activeTab === "flood" && <FloodModerationQueue />}
  </div>;
}
