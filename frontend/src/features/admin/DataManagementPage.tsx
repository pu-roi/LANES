"use client";

import React, { useState } from "react";
import { Download, Database, RefreshCw, Trash2, ShieldAlert } from "lucide-react";
import toast from "react-hot-toast";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { Card, CardHeader, CardTitle, CardContent } from "@/shared/ui";
import { Button } from "@/shared/ui";
import { ConfirmDialog, DatePicker, TableActionGroup, TableActionButton } from "@/shared/ui";
import { apiClient } from "@/lib/apiClient";
import { parseUtcDate } from "@/lib/utils";
import { getBackups, createBackup, restoreBackup, deleteBackup, cleanupData, BackupFile } from "./adminApi";

function formatBytes(bytes: number, decimals = 1): string {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

export default function DataManagementPage() {
  const queryClient = useQueryClient();

  // Restore state
  const [restoreId, setRestoreId] = useState<string | null>(null);
  const [isRestoreModalOpen, setIsRestoreModalOpen] = useState(false);

  // Delete backup state
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  // Cleanup state
  const [cleanupFrom, setCleanupFrom] = useState("");
  const [cleanupTo, setCleanupTo] = useState("");
  const [isCleanupModalOpen, setIsCleanupModalOpen] = useState(false);

  // Downloading state
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const { data: backups = [], isLoading: isBackupsLoading } = useQuery({
    queryKey: ["adminBackups"],
    queryFn: getBackups,
  });

  const selectedRestoreBackup = backups.find((b) => b.id === restoreId);
  const selectedDeleteBackup = backups.find((b) => b.id === deleteId);

  const createBackupMutation = useMutation({
    mutationFn: createBackup,
    onSuccess: () => {
      toast.success("Backup created successfully");
      queryClient.invalidateQueries({ queryKey: ["adminBackups"] });
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to create backup");
    }
  });

  const restoreBackupMutation = useMutation({
    mutationFn: ({ backupId, confirm }: { backupId: string; confirm: boolean }) => restoreBackup(backupId, confirm),
    onSuccess: () => {
      toast.success("Database restored successfully");
      queryClient.invalidateQueries({ queryKey: ["adminBackups"] });
      // Invalidate all platform caches to refetch cleanly restored data
      queryClient.invalidateQueries();
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to restore database");
    }
  });

  const deleteBackupMutation = useMutation({
    mutationFn: (backupId: string) => deleteBackup(backupId),
    onSuccess: () => {
      toast.success("Backup deleted successfully");
      queryClient.invalidateQueries({ queryKey: ["adminBackups"] });
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to delete backup");
    }
  });

  const cleanupMutation = useMutation({
    mutationFn: ({ from, to }: { from: string; to: string }) => cleanupData(from, to, true),
    onSuccess: (res) => {
      toast.success(res.detail || "Data cleaned up successfully");
      setCleanupFrom("");
      setCleanupTo("");
      setIsCleanupModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ["adminBackups"] });
      queryClient.invalidateQueries({ queryKey: ["adminReports"] });
      queryClient.invalidateQueries({ queryKey: ["adminZones"] });
      queryClient.invalidateQueries({ queryKey: ["activeZones"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to cleanup data");
    }
  });

  const isMutating = 
    createBackupMutation.isPending || 
    restoreBackupMutation.isPending || 
    deleteBackupMutation.isPending || 
    cleanupMutation.isPending;

  const isLoading = isBackupsLoading || isMutating || Boolean(downloadingId);

  const isDateRangeInvalid = Boolean(
    cleanupFrom && cleanupTo && new Date(cleanupFrom) > new Date(cleanupTo)
  );

  const handleCreateBackup = () => {
    createBackupMutation.mutate();
  };

  const handleRestore = () => {
    if (!restoreId) return;
    restoreBackupMutation.mutate({ backupId: restoreId, confirm: true }, {
      onSettled: () => {
        setIsRestoreModalOpen(false);
        setRestoreId(null);
      }
    });
  };

  const handleDeleteBackup = () => {
    if (!deleteId) return;
    deleteBackupMutation.mutate(deleteId, {
      onSettled: () => {
        setIsDeleteModalOpen(false);
        setDeleteId(null);
      }
    });
  };

  const handleCleanup = () => {
    if (!cleanupFrom || !cleanupTo || isDateRangeInvalid) return;
    cleanupMutation.mutate({
      from: new Date(cleanupFrom).toISOString(),
      to: new Date(cleanupTo).toISOString()
    });
  };

  const downloadExport = async (type: "reports" | "zones", format: "csv" | "json") => {
    try {
      const filename = `${type}_export_${new Date().toISOString().split('T')[0]}.${format}`;
      await apiClient.download(`/admin/data/export/${type}?format=${format}`, filename);
      toast.success(`${type} exported successfully`);
    } catch (error: any) {
      toast.error(error.message || `Failed to export ${type}`);
    }
  };

  const downloadBackupFile = async (backupId: string, filename: string) => {
    try {
      setDownloadingId(backupId);
      await apiClient.download(`/admin/data/backups/${backupId}/download`, filename);
      toast.success("Backup downloaded successfully");
    } catch (error: any) {
      toast.error(error.message || "Failed to download backup");
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div className="w-full max-w-[1600px] mx-auto space-y-6 pb-[calc(var(--bottom-nav-height,1rem)+env(safe-area-inset-bottom,1rem))]">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Data Management</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Export Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Download className="w-5 h-5 text-blue-600" />
              Data Export
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-600">
              Download system data with PostGIS spatial coordinates for offline analysis or external reporting.
            </p>
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-2 items-start sm:items-center justify-between p-3 bg-slate-50 rounded-lg">
                <span className="font-medium text-slate-700">Flood Reports</span>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => downloadExport("reports", "csv")}>CSV</Button>
                  <Button variant="outline" size="sm" onClick={() => downloadExport("reports", "json")}>JSON</Button>
                </div>
              </div>
              <div className="flex flex-col sm:flex-row gap-2 items-start sm:items-center justify-between p-3 bg-slate-50 rounded-lg">
                <span className="font-medium text-slate-700">Avoidance Zones</span>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => downloadExport("zones", "csv")}>CSV</Button>
                  <Button variant="outline" size="sm" onClick={() => downloadExport("zones", "json")}>JSON</Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Cleanup Section */}
        <Card className="border-red-100 overflow-visible">
          <CardHeader className="rounded-t-xl">
            <CardTitle className="flex items-center gap-2 text-red-600">
              <Trash2 className="w-5 h-5" />
              Data Cleanup
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-600">
              Permanently delete old reports and zones to free up database space. Community feed posts are preserved.
            </p>
            <div className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <DatePicker
                  label="From Date"
                  value={cleanupFrom}
                  onChange={(e) => setCleanupFrom(e.target.value)}
                />
                <DatePicker
                  label="To Date"
                  value={cleanupTo}
                  onChange={(e) => setCleanupTo(e.target.value)}
                />
              </div>
              {isDateRangeInvalid && (
                <p className="text-xs text-red-500 font-medium">
                  &apos;From Date&apos; must be before or equal to &apos;To Date&apos;.
                </p>
              )}
              <Button
                variant="danger"
                className="w-full"
                disabled={!cleanupFrom || !cleanupTo || isDateRangeInvalid || isLoading}
                onClick={() => setIsCleanupModalOpen(true)}
              >
                Delete Records
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Backup Section */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-600" />
            Database Backups
          </CardTitle>
          <Button
            variant="primary"
            onClick={handleCreateBackup}
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Create Backup
          </Button>
        </CardHeader>
        <CardContent>
          {backups.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              No backups found. Create one to get started.
            </div>
          ) : (
            <>
              {/* Desktop Table View */}
              <div className="hidden md:block overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="text-xs text-slate-500 uppercase bg-slate-50">
                    <tr>
                      <th className="px-4 py-3 rounded-tl-lg">Filename</th>
                      <th className="px-4 py-3">Size</th>
                      <th className="px-4 py-3">Created At</th>
                      <th className="px-4 py-3 rounded-tr-lg text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {backups.map((backup) => (
                      <tr key={backup.id} className="border-b last:border-0 hover:bg-slate-50">
                        <td className="px-4 py-3 font-medium text-slate-900">{backup.name}</td>
                        <td className="px-4 py-3 text-slate-600">{formatBytes(backup.size_bytes)}</td>
                        <td className="px-4 py-3 text-slate-600">
                          {parseUtcDate(backup.created_at)?.toLocaleString() || backup.created_at}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <TableActionGroup>
                            <TableActionButton
                              actionVariant="download"
                              disabled={isLoading}
                              onClick={() => downloadBackupFile(backup.id, backup.name)}
                            >
                              {downloadingId === backup.id ? "Downloading..." : "Download"}
                            </TableActionButton>
                            <TableActionButton
                              actionVariant="restore"
                              disabled={isLoading}
                              onClick={() => {
                                setRestoreId(backup.id);
                                setIsRestoreModalOpen(true);
                              }}
                            >
                              Restore
                            </TableActionButton>
                            <TableActionButton
                              actionVariant="delete"
                              disabled={isLoading}
                              onClick={() => {
                                setDeleteId(backup.id);
                                setIsDeleteModalOpen(true);
                              }}
                            >
                              Delete
                            </TableActionButton>
                          </TableActionGroup>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Mobile Card List View (PWA Responsive) */}
              <div className="block md:hidden space-y-3">
                {backups.map((backup) => (
                  <div key={backup.id} className="p-4 bg-slate-50 rounded-lg border border-slate-200/80 space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="font-medium text-slate-900 text-sm break-all">{backup.name}</div>
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 flex-shrink-0">
                        {formatBytes(backup.size_bytes)}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500">
                      {parseUtcDate(backup.created_at)?.toLocaleString() || backup.created_at}
                    </div>
                    <div className="flex gap-2 pt-1 border-t border-slate-200">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 text-xs"
                        disabled={isLoading}
                        onClick={() => downloadBackupFile(backup.id, backup.name)}
                      >
                        {downloadingId === backup.id ? "Downloading..." : "Download"}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 text-xs text-amber-700 hover:bg-amber-50"
                        disabled={isLoading}
                        onClick={() => {
                          setRestoreId(backup.id);
                          setIsRestoreModalOpen(true);
                        }}
                      >
                        Restore
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 text-xs text-red-600 hover:bg-red-50"
                        disabled={isLoading}
                        onClick={() => {
                          setDeleteId(backup.id);
                          setIsDeleteModalOpen(true);
                        }}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Restore Confirmation Dialog */}
      <ConfirmDialog
        isOpen={isRestoreModalOpen}
        title="Restore Database"
        message={
          <div className="space-y-3">
            <p>Are you sure you want to restore the database from this backup?</p>
            {selectedRestoreBackup && (
              <div className="bg-slate-50 p-3 rounded-lg text-xs space-y-1 font-mono text-slate-700 border border-slate-200">
                <div><strong>File:</strong> {selectedRestoreBackup.name}</div>
                <div><strong>Size:</strong> {formatBytes(selectedRestoreBackup.size_bytes)}</div>
                <div><strong>Created:</strong> {parseUtcDate(selectedRestoreBackup.created_at)?.toLocaleString() || selectedRestoreBackup.created_at}</div>
              </div>
            )}
            <div className="p-3 bg-amber-50 text-amber-800 rounded-md flex items-start gap-2">
              <ShieldAlert className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <p className="text-sm">
                <strong>WARNING:</strong> This action will overwrite the current database state.
                Any data created after this backup was taken will be permanently replaced.
              </p>
            </div>
          </div>
        }
        confirmLabel="Yes, Restore Database"
        cancelLabel="Cancel"
        onConfirm={handleRestore}
        onCancel={() => {
          setIsRestoreModalOpen(false);
          setRestoreId(null);
        }}
        variant="destructive"
        isLoading={isLoading}
      />

      {/* Cleanup Confirmation Dialog */}
      <ConfirmDialog
        isOpen={isCleanupModalOpen}
        title="Delete Data"
        message={
          <div className="space-y-2">
            <p>Are you sure you want to permanently delete data from <strong>{cleanupFrom}</strong> to <strong>{cleanupTo}</strong>?</p>
            <p className="text-sm text-slate-600">
              This will remove flood reports and avoidance zones in this date range. Citizen community posts will be preserved. This action cannot be undone.
            </p>
          </div>
        }
        confirmLabel="Yes, Delete Data"
        cancelLabel="Cancel"
        onConfirm={handleCleanup}
        onCancel={() => setIsCleanupModalOpen(false)}
        variant="destructive"
        isLoading={isLoading}
      />

      {/* Delete Backup Confirmation Dialog */}
      <ConfirmDialog
        isOpen={isDeleteModalOpen}
        title="Delete Backup"
        message={
          <div className="space-y-3">
            <p>Are you sure you want to permanently delete this database backup? This action cannot be undone.</p>
            {selectedDeleteBackup && (
              <div className="bg-slate-50 p-3 rounded-lg text-xs space-y-1 font-mono text-slate-700 border border-slate-200">
                <div><strong>File:</strong> {selectedDeleteBackup.name}</div>
                <div><strong>Size:</strong> {formatBytes(selectedDeleteBackup.size_bytes)}</div>
              </div>
            )}
          </div>
        }
        confirmLabel="Yes, Delete Backup"
        cancelLabel="Cancel"
        onConfirm={handleDeleteBackup}
        onCancel={() => {
          setIsDeleteModalOpen(false);
          setDeleteId(null);
        }}
        variant="destructive"
        isLoading={isLoading}
      />
    </div>
  );
}
