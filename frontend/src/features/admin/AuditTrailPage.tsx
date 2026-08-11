"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { getAuditLogs, AuditLogRecord } from "./adminApi";
import { Button } from "@/shared/ui/Button";
import { Modal } from "@/shared/ui/Modal";
import { Select, Pagination, DataTable, Column } from "@/shared/ui";
import {
  Loader2,
  FileCode,
  Search,
  ChevronLeft,
  ChevronRight,
  Shield,
  RefreshCw,
  Eye,
  Calendar,
  Globe,
  Activity,
  Download
} from "lucide-react";

const LIMIT = 10;

const ACTION_BADGES: Record<string, { bg: string; text: string; label: string; module: string }> = {
  LOGIN_SUCCESS: { bg: "bg-emerald-50 border-emerald-200", text: "text-emerald-700", label: "Login Success", module: "Authentication" },
  LOGIN_FAILURE: { bg: "bg-rose-50 border-rose-200", text: "text-rose-700", label: "Login Failure", module: "Authentication" },
  LOGOUT: { bg: "bg-slate-50 border-slate-200", text: "text-slate-700", label: "Logout", module: "Authentication" },
  APPROVE_REPORT: { bg: "bg-blue-50 border-blue-200", text: "text-blue-700", label: "Approve Report", module: "Flood Reports" },
  REJECT_REPORT: { bg: "bg-amber-50 border-amber-200", text: "text-amber-700", label: "Reject Report", module: "Flood Reports" },
  DEACTIVATE_ZONE: { bg: "bg-orange-50 border-orange-200", text: "text-orange-700", label: "Deactivate Zone", module: "Active Zones Map" },
  DEACTIVATE_ZONES_BULK: { bg: "bg-violet-50 border-violet-200", text: "text-violet-700", label: "Bulk Deactivate", module: "Active Zones Map" },
  UPDATE_USER_STATUS: { bg: "bg-sky-50 border-sky-200", text: "text-sky-700", label: "Update User", module: "Users Management" },
  DELETE_USER: { bg: "bg-red-50 border-red-200", text: "text-red-700", label: "Delete User", module: "Users Management" },
  CREATE_BACKUP: { bg: "bg-teal-50 border-teal-200", text: "text-teal-700", label: "Create Backup", module: "Data Management" },
  DELETE_BACKUP: { bg: "bg-red-50 border-red-200", text: "text-red-700", label: "Delete Backup", module: "Data Management" },
  RESTORE_BACKUP: { bg: "bg-indigo-50 border-indigo-200", text: "text-indigo-700", label: "Restore Backup", module: "Data Management" },
  CLEANUP_DATABASE: { bg: "bg-purple-50 border-purple-200", text: "text-purple-700", label: "Clear Data", module: "Data Management" },
};

export default function AuditTrailPage() {
  const [page, setPage] = useState(1);
  const [actionType, setActionType] = useState("all");
  const [inspectLog, setInspectLog] = useState<AuditLogRecord | null>(null);

  const { data, isLoading, refetch, isPlaceholderData } = useQuery({
    queryKey: ["adminAuditLogs", page, actionType],
    queryFn: () => getAuditLogs(page, LIMIT, actionType === "all" ? undefined : actionType),
    placeholderData: (prev) => prev,
    refetchInterval: 30000, // Auto-refresh logs every 30 seconds (AJAX Polling)
  });

  // Force a refetch whenever this page is visited/mounted
  useEffect(() => {
    refetch();
  }, [refetch]);

  const logs = data?.logs || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / LIMIT);

  const handleActionChange = (e: { target: { value: string | number } }) => {
    setActionType(String(e.target.value));
    setPage(1);
  };

  const handleExportCSV = () => {
    if (logs.length === 0) return;
    const headers = ["Timestamp", "Operator", "Email", "Action Type", "Target Table", "Target ID", "IP Address", "Metadata"];
    const rows = logs.map((log) => [
      new Date(log.created_at).toISOString(),
      log.admin ? log.admin.username : "System",
      log.admin ? log.admin.email : "",
      log.action_type,
      log.target_table || "",
      log.target_id || "",
      log.ip_address || "",
      JSON.stringify(log.metadata_json || {})
    ]);
    const csvContent = [headers.join(","), ...rows.map((r) => r.map((val) => `"${String(val).replace(/"/g, '""')}"`).join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `lanes_audit_log_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const auditColumns: Column<AuditLogRecord>[] = [
    {
      key: 'created_at',
      title: 'Timestamp',
      sortable: true,
      className: 'whitespace-nowrap text-center',
      render: (log) => (
        <div className="flex justify-center items-center gap-2 whitespace-nowrap">
          <Calendar className="w-4 h-4 text-gray-400" />
          <span className="text-sm font-medium text-gray-700">
            {new Date(log.created_at).toLocaleString()}
          </span>
        </div>
      )
    },
    {
      key: 'operator',
      title: 'Operator',
      sortable: true,
      className: 'whitespace-nowrap',
      sortFn: (a, b) => {
        const aName = a.admin?.username || "";
        const bName = b.admin?.username || "";
        return aName.localeCompare(bName);
      },
      render: (log) => (
        <div className="whitespace-nowrap">
          {log.admin ? (
            <div>
              <p className="text-sm font-semibold text-gray-900">{log.admin.username}</p>
              <p className="text-xs text-gray-500 font-medium">{log.admin.email}</p>
            </div>
          ) : (
            <span className="text-sm text-gray-400 italic">System / Anonymous</span>
          )}
        </div>
      )
    },
    {
      key: 'source_module',
      title: 'Source Module',
      sortable: true,
      className: 'whitespace-nowrap text-center',
      sortFn: (a, b) => {
        const aModule = ACTION_BADGES[a.action_type]?.module || "System Component";
        const bModule = ACTION_BADGES[b.action_type]?.module || "System Component";
        return aModule.localeCompare(bModule);
      },
      render: (log) => {
        const badge = ACTION_BADGES[log.action_type] || { module: "System Component" };
        return (
          <span className="whitespace-nowrap text-xs font-semibold text-gray-600 bg-gray-100 px-2.5 py-1 rounded-md border border-gray-200 shadow-sm">
            {badge.module}
          </span>
        );
      }
    },
    {
      key: 'action_type',
      title: 'Action Type',
      sortable: true,
      className: 'whitespace-nowrap text-center',
      render: (log) => {
        const badge = ACTION_BADGES[log.action_type] || {
          bg: "bg-gray-50 border-gray-200",
          text: "text-gray-700",
          label: log.action_type,
        };
        return (
          <span className={`whitespace-nowrap inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold border ${badge.bg} ${badge.text}`}>
            {badge.label}
          </span>
        );
      }
    },
    {
      key: 'target',
      title: 'Target',
      sortable: true,
      className: 'whitespace-nowrap text-center',
      sortFn: (a, b) => (a.target_table || "").localeCompare(b.target_table || ""),
      render: (log) => (
        <div className="whitespace-nowrap">
          {log.target_id ? (
            <div className="text-sm">
              <span className="font-semibold text-gray-700">{log.target_table}</span>
              <span className="text-gray-400 ml-1">#{log.target_id}</span>
            </div>
          ) : (
            <span className="text-sm text-gray-400 font-medium">-</span>
          )}
        </div>
      )
    },
    {
      key: 'ip_address',
      title: 'IP Address',
      sortable: true,
      className: 'whitespace-nowrap text-center',
      render: (log) => (
        <div className="whitespace-nowrap">
          {log.ip_address ? (
            <div className="flex items-center justify-center gap-1.5 text-sm text-gray-600 font-medium">
              <Globe className="w-3.5 h-3.5 text-gray-400" />
              {log.ip_address}
            </div>
          ) : (
            <span className="text-sm text-gray-400 font-medium">-</span>
          )}
        </div>
      )
    },
    {
      key: 'details',
      title: 'Details',
      sortable: false,
      className: 'whitespace-nowrap text-center',
      render: (log) => (
        <div className="flex justify-center whitespace-nowrap">
          <Button
            onClick={() => setInspectLog(log)}
            variant="outline"
            size="sm"
            className="inline-flex items-center gap-1.5 text-xs text-gray-600 hover:text-gray-900 border border-gray-200 shadow-sm"
          >
            <Eye className="w-3.5 h-3.5" />
            Inspect
          </Button>
        </div>
      )
    }
  ];

  return (
    <div className="w-full max-w-[1600px] mx-auto space-y-6 text-gray-900">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">System Audit Trail</h1>
          <p className="text-gray-500 text-sm mt-1">
            Access logs, moderation reviews, and configuration edits logged chronologically.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={handleExportCSV}
            disabled={logs.length === 0}
            className="flex items-center gap-2 text-sm"
          >
            <Download className="w-4 h-4" />
            Export to CSV
          </Button>
          <Button
            onClick={() => refetch()}
            variant="outline"
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh Logs
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Activity className="w-5 h-5 text-gray-400 shrink-0" />
          <span className="text-sm font-semibold text-gray-700">Filter Activity:</span>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
          <Select
            value={actionType}
            onChange={handleActionChange}
            className="w-full sm:w-56 font-medium"
            options={[
              { label: "All Actions", value: "all" },
              { label: "Login Success", value: "LOGIN_SUCCESS" },
              { label: "Login Failure", value: "LOGIN_FAILURE" },
              { label: "Approve Report", value: "APPROVE_REPORT" },
              { label: "Reject Report", value: "REJECT_REPORT" },
              { label: "Deactivate Zone", value: "DEACTIVATE_ZONE" },
              { label: "Bulk Deactivate", value: "DEACTIVATE_ZONES_BULK" },
              { label: "Update User Status", value: "UPDATE_USER_STATUS" },
              { label: "Delete User", value: "DELETE_USER" }
            ]}
          />
        </div>
      </div>

      {/* Logs Table */}
      {isLoading ? (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col items-center justify-center py-20 gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <p className="text-sm text-gray-500 font-medium">Fetching audit logs...</p>
        </div>
      ) : (
        <div className={`transition-opacity duration-150 ${isPlaceholderData ? "opacity-60" : "opacity-100"}`}>
          <DataTable
            columns={auditColumns}
            data={logs}
            keyExtractor={(log) => log.id}
            pagination={{ page, totalPages, onPageChange: setPage, disabled: isPlaceholderData }}
            emptyState={
              <div className="flex flex-col items-center justify-center py-16 gap-3 text-center px-4">
                <div className="p-3 bg-gray-50 rounded-full">
                  <Shield className="w-8 h-8 text-gray-400" />
                </div>
                <h3 className="text-gray-800 font-bold text-lg">No Audit Records Found</h3>
                <p className="text-sm text-gray-500 max-w-sm">
                  We couldn't find any system audit trail events matching your current filter settings.
                </p>
              </div>
            }
          />
        </div>
      )}

      {/* Inspection Modal */}
      <Modal
        isOpen={inspectLog !== null}
        onClose={() => setInspectLog(null)}
        title="Audit Event Inspector"
      >
        {inspectLog && (
          <div className="space-y-4 text-gray-900">
            <div className="grid grid-cols-2 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-100 text-sm">
              <div>
                <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Timestamp</p>
                <p className="font-semibold text-gray-800 mt-0.5">
                  {new Date(inspectLog.created_at).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Action Type</p>
                <p className="font-semibold text-gray-800 mt-0.5">{inspectLog.action_type}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Operator</p>
                <p className="font-semibold text-gray-800 mt-0.5">
                  {inspectLog.admin ? inspectLog.admin.username : "System / Scraper"}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Source Module</p>
                <p className="font-semibold text-gray-800 mt-0.5">
                  {ACTION_BADGES[inspectLog.action_type]?.module || "System Component"}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-400 font-bold uppercase tracking-wider">Origin IP</p>
                <p className="font-semibold text-gray-800 mt-0.5">
                  {inspectLog.ip_address || "Unavailable"}
                </p>
              </div>
            </div>

            <div>
              <p className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <FileCode className="w-4 h-4 text-gray-400" />
                Metadata Payload (JSONB)
              </p>
              <pre className="bg-neutral-900 text-neutral-100 p-4 rounded-xl text-xs overflow-x-auto border border-neutral-800 font-mono shadow-inner leading-relaxed">
                {JSON.stringify(inspectLog.metadata_json, null, 2)}
              </pre>
            </div>

            <div className="flex justify-end pt-2">
              <Button onClick={() => setInspectLog(null)} className="px-5 text-sm">
                Close Inspector
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
