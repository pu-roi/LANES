"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { format } from "date-fns";
import {
  getReports,
  getUsers,
  getZones,
  restoreReport,
  hardDeleteReport,
  restoreZone,
  hardDeleteZone,
  restoreUser,
  hardDeleteUser,
  purgeExpiredArchiveRecords,
  getArchivedPosts,
  restorePost,
  hardDeletePost,
  FloodReport,
  UserRecord,
  AvoidanceZone,
  ArchivedPost,
} from "@/features/admin/adminApi";
import { Button, Tabs, Input, DataTable, Column, useToast } from "@/shared/ui";
import {
  Loader2,
  Archive,
  Search,
  RefreshCw,
  AlertTriangle,
  FileText,
  Users,
  Layers,
  ShieldAlert,
  RotateCcw,
  Trash2,
  Eye,
  MessageSquare,
  EyeOff,
} from "lucide-react";
import { ReportDetailsModal } from "@/features/admin/components/ReportDetailsModal";
import { ZoneDetailsModal } from "./components/ZoneDetailsModal";
import { PostDetailsModal } from "./components/PostDetailsModal";
import { TypedDeleteModal } from "./components/TypedDeleteModal";

const LIMIT = 10;

type MainTab = "users" | "spatial" | "posts";
type SpatialSubTab = "reports" | "zones";
type PostSubTab = "deleted" | "hidden";

export default function ArchivePage() {
  const queryClient = useQueryClient();
  const toast = useToast();

  const [activeTab, setActiveTab] = useState<MainTab>("spatial");
  const [spatialSubTab, setSpatialSubTab] = useState<SpatialSubTab>("reports");
  const [postSubTab, setPostSubTab] = useState<PostSubTab>("deleted");
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  // Modals state
  const [detailsReport, setDetailsReport] = useState<FloodReport | null>(null);
  const [detailsZone, setDetailsZone] = useState<AvoidanceZone | null>(null);
  const [detailsPost, setDetailsPost] = useState<ArchivedPost | null>(null);
  const [hardDeleteTarget, setHardDeleteTarget] = useState<{
    type: "report" | "zone" | "post" | "user";
    id: number;
    name: string;
  } | null>(null);

  // Queries
  const {
    data: usersData,
    isLoading: usersLoading,
    refetch: refetchUsers,
    isPlaceholderData: usersPlaceholder,
  } = useQuery({
    queryKey: ["archivedUsers", page, search],
    queryFn: () => getUsers(page, LIMIT, search, "all", true),
    enabled: activeTab === "users",
    placeholderData: (prev) => prev,
  });

  const {
    data: reportsData,
    isLoading: reportsLoading,
    refetch: refetchReports,
    isPlaceholderData: reportsPlaceholder,
  } = useQuery({
    queryKey: ["archivedReports", page, search],
    queryFn: () => getReports({ page, limit: LIMIT, search, archived: true }),
    enabled: activeTab === "spatial" && spatialSubTab === "reports",
    placeholderData: (prev) => prev,
  });

  const {
    data: zonesData,
    isLoading: zonesLoading,
    refetch: refetchZones,
    isPlaceholderData: zonesPlaceholder,
  } = useQuery({
    queryKey: ["archivedZones", page, search],
    queryFn: () => getZones({ page, limit: LIMIT, archived: true, search }),
    enabled: activeTab === "spatial" && spatialSubTab === "zones",
    placeholderData: (prev) => prev,
  });

  const {
    data: postsData,
    isLoading: postsLoading,
    refetch: refetchPosts,
    isPlaceholderData: postsPlaceholder,
  } = useQuery({
    queryKey: ["archivedPosts", postSubTab, page, search],
    queryFn: () => getArchivedPosts(page, LIMIT, postSubTab, search),
    enabled: activeTab === "posts",
    placeholderData: (prev) => prev,
  });

  // Mutations
  const restoreReportMutation = useMutation({
    mutationFn: (id: number) => restoreReport(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["archivedReports"] });
      queryClient.invalidateQueries({ queryKey: ["adminPendingReports"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
      toast.success("Report Restored", `Flood report #${data.id} has been restored to the pending moderation queue.`);
      setDetailsReport(null);
    },
    onError: (err: any) => {
      toast.error("Restore Failed", err?.response?.data?.detail || err?.message || "Could not restore report.");
    },
  });

  const hardDeleteReportMutation = useMutation({
    mutationFn: (id: number) => hardDeleteReport(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["archivedReports"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
      toast.success("Report Deleted", `Flood report #${data.id} was permanently deleted.`);
      setHardDeleteTarget(null);
      setDetailsReport(null);
    },
    onError: (err: any) => {
      toast.error("Delete Failed", err?.response?.data?.detail || err?.message || "Could not delete report.");
    },
  });

  const restoreZoneMutation = useMutation({
    mutationFn: (id: number) => restoreZone(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["archivedZones"] });
      queryClient.invalidateQueries({ queryKey: ["adminZones"] });
      queryClient.invalidateQueries({ queryKey: ["activeZonesMap"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
      toast.success("Zone Reactivated", `Avoidance zone #${data.id} has been restored and reactivated.`);
      setDetailsZone(null);
    },
    onError: (err: any) => {
      toast.error("Restore Failed", err?.response?.data?.detail || err?.message || "Could not restore zone.");
    },
  });

  const hardDeleteZoneMutation = useMutation({
    mutationFn: (id: number) => hardDeleteZone(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["archivedZones"] });
      queryClient.invalidateQueries({ queryKey: ["adminZones"] });
      queryClient.invalidateQueries({ queryKey: ["activeZonesMap"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
      toast.success("Zone Deleted", `Avoidance zone #${data.id} was permanently deleted.`);
      setHardDeleteTarget(null);
      setDetailsZone(null);
    },
    onError: (err: any) => {
      toast.error("Delete Failed", err?.response?.data?.detail || err?.message || "Could not delete zone.");
    },
  });

  const restorePostMutation = useMutation({
    mutationFn: (id: number) => restorePost(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["archivedPosts"] });
      queryClient.invalidateQueries({ queryKey: ["feed"] });
      toast.success("Post Restored", `Post #${data.id} has been restored to the community feed.`);
      setDetailsPost(null);
    },
    onError: (err: any) => {
      toast.error("Restore Failed", err?.response?.data?.detail || err?.message || "Could not restore post.");
    },
  });

  const hardDeletePostMutation = useMutation({
    mutationFn: (id: number) => hardDeletePost(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["archivedPosts"] });
      toast.success("Post Deleted", `Post #${data.id} was permanently deleted.`);
      setHardDeleteTarget(null);
      setDetailsPost(null);
    },
    onError: (err: any) => {
      toast.error("Delete Failed", err?.response?.data?.detail || err?.message || "Could not delete post.");
    },
  });

  const restoreUserMutation = useMutation({
    mutationFn: (id: number) => restoreUser(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["archivedUsers"] });
      queryClient.invalidateQueries({ queryKey: ["adminUsers"] });
      toast.success("User Restored", `User @${data.username} has been restored successfully.`);
    },
    onError: (err: any) => {
      toast.error("Restore Failed", err?.response?.data?.detail || err?.message || "Could not restore user account.");
    },
  });

  const hardDeleteUserMutation = useMutation({
    mutationFn: (id: number) => hardDeleteUser(id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["archivedUsers"] });
      toast.success("User Deleted", `User was permanently deleted from the database.`);
      setHardDeleteTarget(null);
    },
    onError: (err: any) => {
      toast.error("Delete Failed", err?.response?.data?.detail || err?.message || "Could not delete user account.");
    },
  });

  const purgeExpiredMutation = useMutation({
    mutationFn: () => purgeExpiredArchiveRecords(30),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["archivedUsers"] });
      queryClient.invalidateQueries({ queryKey: ["archivedReports"] });
      queryClient.invalidateQueries({ queryKey: ["archivedZones"] });
      queryClient.invalidateQueries({ queryKey: ["archivedPosts"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
      toast.success("Auto-Purge Completed", `Purged ${data.results.total} records older than 30 days.`);
    },
    onError: (err: any) => {
      toast.error("Purge Failed", err?.response?.data?.detail || err?.message || "Failed to purge expired records.");
    },
  });

  const getRetentionBadge = (archivedDateStr?: string | null) => {
    if (!archivedDateStr) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-600">
          30-day retention
        </span>
      );
    }
    const archivedDate = new Date(archivedDateStr);
    const now = new Date();
    const elapsedDays = Math.floor((now.getTime() - archivedDate.getTime()) / (1000 * 60 * 60 * 24));
    const remainingDays = Math.max(0, 30 - elapsedDays);

    if (remainingDays <= 3) {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-red-100 text-red-700 border border-red-200">
          Auto-purges in {remainingDays} {remainingDays === 1 ? "day" : "days"}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
        Auto-purges in {remainingDays} days
      </span>
    );
  };

  const handleExecuteHardDelete = () => {
    if (!hardDeleteTarget) return;
    if (hardDeleteTarget.type === "report") {
      hardDeleteReportMutation.mutate(hardDeleteTarget.id);
    } else if (hardDeleteTarget.type === "zone") {
      hardDeleteZoneMutation.mutate(hardDeleteTarget.id);
    } else if (hardDeleteTarget.type === "post") {
      hardDeletePostMutation.mutate(hardDeleteTarget.id);
    } else if (hardDeleteTarget.type === "user") {
      hardDeleteUserMutation.mutate(hardDeleteTarget.id);
    }
  };

  const isHardDeleteLoading =
    hardDeleteReportMutation.isPending ||
    hardDeleteZoneMutation.isPending ||
    hardDeletePostMutation.isPending ||
    hardDeleteUserMutation.isPending;

  // Pagination & Counts
  const users = usersData?.users || [];
  const totalUsers = usersData?.total || 0;
  const usersTotalPages = Math.ceil(totalUsers / LIMIT);

  const reports = reportsData?.reports || [];
  const totalReports = reportsData?.total || 0;
  const reportsTotalPages = Math.ceil(totalReports / LIMIT);

  const zones = zonesData?.zones || [];
  const totalZones = zonesData?.total || 0;
  const zonesTotalPages = Math.ceil(totalZones / LIMIT);

  const posts = postsData?.posts || [];
  const totalPosts = postsData?.total || 0;
  const postsTotalPages = Math.ceil(totalPosts / LIMIT);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
    setPage(1);
  };

  const handleMainTabChange = (tab: MainTab) => {
    setActiveTab(tab);
    setPage(1);
    setSearch("");
  };

  const handleRefresh = () => {
    if (activeTab === "users") refetchUsers();
    else if (activeTab === "spatial") {
      if (spatialSubTab === "reports") refetchReports();
      else refetchZones();
    } else if (activeTab === "posts") {
      refetchPosts();
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity?.toLowerCase()) {
      case "extreme":
        return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-200 uppercase">Extreme</span>;
      case "high":
        return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-orange-100 text-orange-800 border border-orange-200 uppercase">High</span>;
      case "medium":
        return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200 uppercase">Medium</span>;
      case "low":
      default:
        return <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-lime-100 text-lime-800 border border-lime-200 uppercase">Low</span>;
    }
  };

  // Table Columns
  const userColumns: Column<UserRecord>[] = [
    {
      key: "id",
      title: "User ID",
      sortable: true,
      className: "whitespace-nowrap text-center",
      render: (user) => <span className="font-mono text-xs font-semibold">#{user.id}</span>,
    },
    {
      key: "username",
      title: "Username",
      sortable: true,
      className: "w-[200px]",
      render: (user) => <span className="font-semibold text-gray-800">{user.username}</span>,
    },
    {
      key: "email",
      title: "Email",
      sortable: true,
      render: (user) => <span className="text-gray-600 font-medium">{user.email}</span>,
    },
    {
      key: "role",
      title: "Role",
      sortable: true,
      className: "whitespace-nowrap text-center",
      render: (user) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
          {user.role?.name || "Unknown"}
        </span>
      ),
    },
    {
      key: "status",
      title: "Retention / Lifecycle",
      sortable: false,
      className: "whitespace-nowrap text-center",
      render: (user) => getRetentionBadge(user.deleted_at),
    },
    {
      key: "actions",
      title: "Actions",
      sortable: false,
      className: "whitespace-nowrap text-right",
      render: (user) => (
        <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => restoreUserMutation.mutate(user.id)}
            disabled={restoreUserMutation.isPending}
            className="h-7 px-2.5 text-xs rounded-lg gap-1 border-emerald-200 text-emerald-600 hover:bg-emerald-50"
            title="Restore User Account"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Restore
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              setHardDeleteTarget({
                type: "user",
                id: user.id,
                name: `User @${user.username} (${user.email})`,
              })
            }
            className="h-7 px-2.5 text-xs rounded-lg gap-1 border-red-200 text-red-600 hover:bg-red-50"
            title="Permanently Delete"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Delete
          </Button>
        </div>
      ),
    },
  ];

  const reportColumns: Column<FloodReport>[] = [
    {
      key: "id",
      title: "Report ID",
      sortable: true,
      className: "whitespace-nowrap text-center",
      render: (report) => <span className="font-mono text-xs font-semibold">#{report.id}</span>,
    },
    {
      key: "severity",
      title: "Severity",
      sortable: true,
      className: "whitespace-nowrap text-center",
      render: (report) => getSeverityBadge(report.severity),
    },
    {
      key: "raw_text",
      title: "Description / Location",
      sortable: false,
      render: (report) => (
        <div className="max-w-md">
          <p className="text-sm font-medium text-gray-900 truncate">
            {report.human_readable_location || report.road_name || (report.barangay ? `Brgy. ${report.barangay}` : "Location not specified")}
          </p>
          <p className="text-xs text-gray-500 truncate mt-0.5">
            {report.raw_text || "No description provided."}
          </p>
        </div>
      ),
    },
    {
      key: "reporter",
      title: "Reporter",
      sortable: false,
      className: "whitespace-nowrap",
      render: (report) => (
        <div className="text-xs">
          <span className="font-semibold text-gray-800">{report.reporter_name || "Anonymous"}</span>
          {report.reporter_trust_score !== undefined && (
            <span className="ml-1.5 px-1.5 py-0.2 rounded bg-blue-50 text-blue-700 font-mono text-[10px]">
              {report.reporter_trust_score} pts
            </span>
          )}
        </div>
      ),
    },
    {
      key: "status",
      title: "Retention / Lifecycle",
      sortable: false,
      className: "whitespace-nowrap text-center",
      render: (report) => getRetentionBadge(report.updated_at),
    },
    {
      key: "actions",
      title: "Actions",
      sortable: false,
      className: "whitespace-nowrap text-right",
      render: (report) => (
        <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setDetailsReport(report)}
            className="h-7 px-2 text-xs rounded-lg gap-1 border-gray-200 text-gray-700 hover:bg-gray-50"
            title="View Details"
          >
            <Eye className="w-3.5 h-3.5" />
            View
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => restoreReportMutation.mutate(report.id)}
            disabled={restoreReportMutation.isPending}
            className="h-7 px-2.5 text-xs rounded-lg gap-1 border-blue-200 text-blue-600 hover:bg-blue-50"
            title="Restore to Pending Moderation Queue"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Restore
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              setHardDeleteTarget({
                type: "report",
                id: report.id,
                name: `Report #${report.id}`,
              })
            }
            className="h-7 px-2.5 text-xs rounded-lg gap-1 border-red-200 text-red-600 hover:bg-red-50"
            title="Permanently Delete"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Delete
          </Button>
        </div>
      ),
    },
  ];

  const zoneColumns: Column<AvoidanceZone>[] = [
    {
      key: "id",
      title: "Zone ID",
      sortable: true,
      className: "whitespace-nowrap text-center",
      render: (zone) => <span className="font-mono text-xs font-semibold">#{zone.id}</span>,
    },
    {
      key: "name",
      title: "Zone Name / Road",
      sortable: true,
      render: (zone) => (
        <div>
          <span className="font-semibold text-gray-900 text-sm">{zone.name || `Avoidance Zone #${zone.id}`}</span>
          {zone.admin_notes && (
            <p className="text-xs text-gray-500 truncate max-w-xs">{zone.admin_notes}</p>
          )}
        </div>
      ),
    },
    {
      key: "severity",
      title: "Severity",
      sortable: true,
      className: "whitespace-nowrap text-center",
      render: (zone) => getSeverityBadge(zone.severity),
    },
    {
      key: "contributors",
      title: "Reports Linked",
      sortable: false,
      className: "whitespace-nowrap text-center",
      render: (zone) => {
        const count = zone.contributors?.length || (zone.report_id ? 1 : 0);
        return (
          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
            {count} report{count === 1 ? "" : "s"}
          </span>
        );
      },
    },
    {
      key: "status",
      title: "Retention / Lifecycle",
      sortable: false,
      className: "whitespace-nowrap text-center",
      render: (zone) => getRetentionBadge(zone.expires_at || zone.created_at),
    },
    {
      key: "actions",
      title: "Actions",
      sortable: false,
      className: "whitespace-nowrap text-right",
      render: (zone) => (
        <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setDetailsZone(zone)}
            className="h-7 px-2 text-xs rounded-lg gap-1 border-gray-200 text-gray-700 hover:bg-gray-50"
            title="View Zone Details"
          >
            <Eye className="w-3.5 h-3.5" />
            View
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => restoreZoneMutation.mutate(zone.id)}
            disabled={restoreZoneMutation.isPending}
            className="h-7 px-2.5 text-xs rounded-lg gap-1 border-blue-200 text-blue-600 hover:bg-blue-50"
            title="Reactivate Avoidance Zone"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reactivate
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              setHardDeleteTarget({
                type: "zone",
                id: zone.id,
                name: `Zone #${zone.id} (${zone.name || "Avoidance Zone"})`,
              })
            }
            className="h-7 px-2.5 text-xs rounded-lg gap-1 border-red-200 text-red-600 hover:bg-red-50"
            title="Permanently Delete"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Delete
          </Button>
        </div>
      ),
    },
  ];


  const postColumns: Column<ArchivedPost>[] = [
    {
      key: "id",
      title: "Post ID",
      sortable: true,
      className: "whitespace-nowrap text-center",
      render: (post: ArchivedPost) => <span className="font-mono text-xs font-semibold">#{post.id}</span>,
    },
    {
      key: "author",
      title: "Author",
      sortable: true,
      className: "w-[180px]",
      render: (post: ArchivedPost) => (
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-xs shrink-0">
            {post.author_avatar ? (
              <img src={post.author_avatar} alt="Avatar" className="w-full h-full rounded-full object-cover" />
            ) : (
              <span>{post.author_name ? post.author_name[0].toUpperCase() : "U"}</span>
            )}
          </div>
          <div className="min-w-0">
            <p className="font-semibold text-gray-900 text-xs truncate max-w-[120px]">{post.author_name}</p>
            <p className="text-[11px] text-gray-400">
              {format(new Date(post.created_at), "MMM d, yyyy")}
            </p>
          </div>
        </div>
      ),
    },
    {
      key: "content",
      title: "Content",
      sortable: false,
      render: (post: ArchivedPost) => (
        <div className="max-w-xs sm:max-w-md">
          <p className="text-xs text-gray-800 line-clamp-2 leading-relaxed">
            {post.content}
          </p>
          {post.media_urls && post.media_urls.length > 0 && (
            <span className="inline-flex items-center gap-1 mt-1 px-1.5 py-0.5 rounded text-[10px] bg-gray-100 text-gray-600 font-medium">
              📷 {post.media_urls.length} media attached
            </span>
          )}
        </div>
      ),
    },
    {
      key: "status",
      title: "Status / Removal",
      sortable: false,
      className: "whitespace-nowrap",
      render: (post: ArchivedPost) => (
        <div className="text-xs">
          {postSubTab === "deleted" ? (
            <div>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-red-100 text-red-800 border border-red-200">
                <Trash2 className="w-3 h-3" /> Soft Deleted
              </span>
              {post.deleted_at && (
                <p className="text-[11px] text-gray-500 mt-0.5">
                  {format(new Date(post.deleted_at), "MMM d, yyyy")}
                </p>
              )}
              {post.deleted_by_name && (
                <p className="text-[10px] text-gray-400">by {post.deleted_by_name}</p>
              )}
            </div>
          ) : (
            <div>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-100 text-amber-800 border border-amber-200">
                <EyeOff className="w-3 h-3" /> Hidden
              </span>
              {post.hidden_at && (
                <p className="text-[11px] text-gray-500 mt-0.5">
                  {format(new Date(post.hidden_at), "MMM d, yyyy")}
                </p>
              )}
              {post.hidden_by_name && (
                <p className="text-[10px] text-gray-400">by {post.hidden_by_name}</p>
              )}
            </div>
          )}
        </div>
      ),
    },
    {
      key: "retention",
      title: "Retention / Lifecycle",
      sortable: false,
      className: "whitespace-nowrap text-center",
      render: (post: ArchivedPost) => getRetentionBadge(post.deleted_at || post.hidden_at),
    },
    {
      key: "location",
      title: "Location",
      sortable: false,
      className: "whitespace-nowrap text-xs text-gray-600",
      render: (post: ArchivedPost) => post.location_tag || "—",
    },
    {
      key: "actions",
      title: "Actions",
      sortable: false,
      className: "whitespace-nowrap text-right",
      render: (post: ArchivedPost) => (
        <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setDetailsPost(post)}
            className="h-7 px-2 text-xs rounded-lg gap-1 border-gray-200 text-gray-700 hover:bg-gray-50"
            title="View Details"
          >
            <Eye className="w-3.5 h-3.5" />
            View
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => restorePostMutation.mutate(post.id)}
            disabled={restorePostMutation.isPending}
            className="h-7 px-2.5 text-xs rounded-lg gap-1 border-emerald-200 text-emerald-600 hover:bg-emerald-50"
            title="Restore Post to Feed"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Restore
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              setHardDeleteTarget({
                type: "post",
                id: post.id,
                name: `Post #${post.id} by ${post.author_name}`,
              })
            }
            className="h-7 px-2.5 text-xs rounded-lg gap-1 border-red-200 text-red-600 hover:bg-red-50"
            title="Permanently Delete"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Delete
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="w-full max-w-[1600px] mx-auto space-y-6 text-gray-900 pb-16">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight flex items-center gap-2">
            <Archive className="w-6 h-6 text-gray-500" />
            Archive Center
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Browse soft-deleted records, rejected flood hazards, and deactivated detour zones for audit and recovery. Records older than 30 days are automatically purged.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button
            onClick={() => purgeExpiredMutation.mutate()}
            disabled={purgeExpiredMutation.isPending}
            variant="outline"
            className="flex items-center gap-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 border-red-200 rounded-xl"
            title="Manually purge records older than 30 days"
          >
            <Trash2 className="w-4 h-4" />
            {purgeExpiredMutation.isPending ? "Purging Expired..." : "Purge Expired (30d+)"}
          </Button>
          <Button
            onClick={handleRefresh}
            variant="outline"
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 rounded-xl"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Main Navigation Tabs */}
      <Tabs<MainTab>
        tabs={[
          { id: "users", label: "Archived Users", icon: Users },
          { id: "spatial", label: "Spatial Data", icon: Layers },
          { id: "posts", label: "Archived Posts", icon: MessageSquare },
        ]}
        activeTab={activeTab}
        onChange={handleMainTabChange}
        variant="underline"
        layoutId="archive-main-tab"
      />

      {/* Spatial Sub-Tabs Header */}
      {activeTab === "spatial" && (
        <div className="flex items-center gap-2 border-b border-gray-200 pb-3">
          <button
            type="button"
            onClick={() => {
              setSpatialSubTab("reports");
              setPage(1);
            }}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all ${
              spatialSubTab === "reports"
                ? "bg-blue-50 text-blue-700 border border-blue-200 shadow-xs"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            <FileText className="w-4 h-4" />
            Archived Reports
          </button>
          <button
            type="button"
            onClick={() => {
              setSpatialSubTab("zones");
              setPage(1);
            }}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all ${
              spatialSubTab === "zones"
                ? "bg-blue-50 text-blue-700 border border-blue-200 shadow-xs"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            Archived Zones
          </button>
        </div>
      )}

      {/* Archived Posts Sub-Tabs Header */}
      {activeTab === "posts" && (
        <div className="flex items-center gap-2 border-b border-gray-200 pb-3">
          <button
            type="button"
            onClick={() => {
              setPostSubTab("deleted");
              setPage(1);
            }}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all ${
              postSubTab === "deleted"
                ? "bg-blue-50 text-blue-700 border border-blue-200 shadow-xs"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            <Trash2 className="w-4 h-4" />
            Deleted Posts
          </button>
          <button
            type="button"
            onClick={() => {
              setPostSubTab("hidden");
              setPage(1);
            }}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-all ${
              postSubTab === "hidden"
                ? "bg-blue-50 text-blue-700 border border-blue-200 shadow-xs"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            <EyeOff className="w-4 h-4" />
            Hidden Posts
          </button>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
        <div className="flex flex-1 gap-3 w-full sm:w-auto">
          <Input
            containerClassName="flex-1 max-w-sm"
            leftIcon={<Search className="w-4 h-4 text-gray-400" />}
            type="text"
            placeholder={
              activeTab === "users"
                ? "Search users..."
                : activeTab === "spatial"
                ? spatialSubTab === "reports"
                  ? "Search reports..."
                  : "Search zones..."
                : "Search posts..."
            }
            value={search}
            onChange={handleSearchChange}
            className="text-gray-900 bg-white"
          />
        </div>

        <div className="text-xs font-semibold text-gray-400">
          Archived records found:{" "}
          <span className="text-gray-900">
            {activeTab === "users"
              ? totalUsers
              : activeTab === "spatial"
              ? spatialSubTab === "reports"
                ? totalReports
                : totalZones
              : totalPosts}
          </span>
        </div>
      </div>

      {/* Data Content */}
      {activeTab === "users" && (
        <div>
          {usersLoading ? (
            <div className="flex flex-col items-center justify-center py-20 bg-white border border-gray-200 rounded-xl shadow-sm">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-2" />
              <p className="text-sm text-gray-500">Loading archived users...</p>
            </div>
          ) : (
            <DataTable
              columns={userColumns}
              data={users}
              keyExtractor={(user) => user.id}
              pagination={{ page, totalPages: usersTotalPages, onPageChange: setPage }}
              emptyState={
                <div className="py-16 text-center">
                  <Archive className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900">No archived users</h3>
                  <p className="text-gray-500 mt-1 max-w-sm mx-auto text-sm">
                    No soft-deleted users were found in the system.
                  </p>
                </div>
              }
            />
          )}
        </div>
      )}

      {activeTab === "spatial" && spatialSubTab === "reports" && (
        <div>
          {reportsLoading ? (
            <div className="flex flex-col items-center justify-center py-20 bg-white border border-gray-200 rounded-xl shadow-sm">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-2" />
              <p className="text-sm text-gray-500">Loading archived reports...</p>
            </div>
          ) : (
            <DataTable
              columns={reportColumns}
              data={reports}
              keyExtractor={(report) => report.id}
              pagination={{ page, totalPages: reportsTotalPages, onPageChange: setPage }}
              emptyState={
                <div className="py-16 text-center">
                  <Archive className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900">No archived reports</h3>
                  <p className="text-gray-500 mt-1 max-w-sm mx-auto text-sm">
                    No rejected or soft-deleted flood reports found.
                  </p>
                </div>
              }
            />
          )}
        </div>
      )}

      {activeTab === "spatial" && spatialSubTab === "zones" && (
        <div>
          {zonesLoading ? (
            <div className="flex flex-col items-center justify-center py-20 bg-white border border-gray-200 rounded-xl shadow-sm">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-2" />
              <p className="text-sm text-gray-500">Loading archived zones...</p>
            </div>
          ) : (
            <DataTable
              columns={zoneColumns}
              data={zones}
              keyExtractor={(zone) => zone.id}
              pagination={{ page, totalPages: zonesTotalPages, onPageChange: setPage }}
              emptyState={
                <div className="py-16 text-center">
                  <ShieldAlert className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900">No archived zones</h3>
                  <p className="text-gray-500 mt-1 max-w-sm mx-auto text-sm">
                    No deactivated or expired avoidance zones found.
                  </p>
                </div>
              }
            />
          )}
        </div>
      )}

      {activeTab === "posts" && (
        <div>
          {postsLoading ? (
            <div className="flex flex-col items-center justify-center py-20 bg-white border border-gray-200 rounded-xl shadow-sm">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-2" />
              <p className="text-sm text-gray-500">
                Loading {postSubTab === "deleted" ? "deleted" : "hidden"} posts...
              </p>
            </div>
          ) : (
            <DataTable
              columns={postColumns}
              data={posts}
              keyExtractor={(post) => post.id}
              pagination={{ page, totalPages: postsTotalPages, onPageChange: setPage }}
              emptyState={
                <div className="py-16 text-center">
                  <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900">
                    No {postSubTab === "deleted" ? "deleted" : "hidden"} posts
                  </h3>
                  <p className="text-gray-500 mt-1 max-w-sm mx-auto text-sm">
                    {postSubTab === "deleted"
                      ? "No soft-deleted community posts found in the archive."
                      : "No moderator-hidden posts found in the archive."}
                  </p>
                </div>
              }
            />
          )}
        </div>
      )}

      {/* Details Modals */}
      <ReportDetailsModal
        report={detailsReport}
        isOpen={detailsReport !== null}
        onClose={() => setDetailsReport(null)}
        onViewOnMap={() => {}}
        onApprove={() => {
          if (detailsReport) {
            restoreReportMutation.mutate(detailsReport.id);
          }
        }}
        isApproveLoading={restoreReportMutation.isPending}
        onOpenMedia={(urls, idx) => {
          if (urls && urls[idx]) {
            window.open(urls[idx], "_blank");
          }
        }}
      />

      <ZoneDetailsModal
        zone={detailsZone}
        isOpen={detailsZone !== null}
        onClose={() => setDetailsZone(null)}
        onRestore={(zone) => restoreZoneMutation.mutate(zone.id)}
        onHardDelete={(zone) =>
          setHardDeleteTarget({
            type: "zone",
            id: zone.id,
            name: `Avoidance Zone #${zone.id}`,
          })
        }
        isRestoring={restoreZoneMutation.isPending}
      />

      <PostDetailsModal
        post={detailsPost}
        isOpen={detailsPost !== null}
        onClose={() => setDetailsPost(null)}
        onRestore={(post) => restorePostMutation.mutate(post.id)}
        onHardDelete={(post) =>
          setHardDeleteTarget({
            type: "post",
            id: post.id,
            name: `Post #${post.id} by ${post.author_name}`,
          })
        }
        isRestoring={restorePostMutation.isPending}
      />

      {/* Typed Confirmation Hard Delete Modal */}
      <TypedDeleteModal
        isOpen={hardDeleteTarget !== null}
        onClose={() => setHardDeleteTarget(null)}
        onConfirm={handleExecuteHardDelete}
        isLoading={isHardDeleteLoading}
        title="Confirm Permanent Deletion"
        itemName={hardDeleteTarget?.name || "this item"}
        itemType={hardDeleteTarget?.type || "record"}
        expectedWord="DELETE"
      />
    </div>
  );
}
