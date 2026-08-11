"use client";

import React, { useState } from "react";
import { Download, Database, RefreshCw, Trash2, ShieldAlert } from "lucide-react";
import toast from "react-hot-toast";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { Card, CardHeader, CardTitle, CardContent } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { ConfirmDialog, DatePicker, TableActionGroup, TableActionButton } from "@/shared/ui";
import { apiClient } from "@/lib/apiClient";
import { getBackups, createBackup, restoreBackup, deleteBackup, cleanupData, BackupFile } from "./adminApi";

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

  const { data: backups = [], isLoading: isBackupsLoading } = useQuery({
    queryKey: ["adminBackups"],
    queryFn: getBackups,
  });

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
      // Invalidate everything to fetch clean restored data
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

  const isLoading = isBackupsLoading || isMutating;

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
    if (!cleanupFrom || !cleanupTo) return;
    cleanupMutation.mutate({
      from: new Date(cleanupFrom).toISOString(),
      to: new Date(cleanupTo).toISOString()
    }, {
      onSettled: () => {
        setIsCleanupModalOpen(false);
        setCleanupFrom("");
        setCleanupTo("");
      }
    });
  };

  const downloadExport = async (type: "reports" | "zones", format: "csv" | "json") => {
    try {
      const filename = `${type}_export_${new Date().toISOString().split('T')[0]}.${format}`;
      await apiClient.download(`/admin/data/export/${type}?format=${format}`, filename);
      toast.success(`${type} exported successfully`);
    } catch (error: any) {
      toast.error(`Failed to export ${type}`);
    }
  };

  const downloadBackupFile = async (backupId: string, filename: string) => {
    try {
      await apiClient.download(`/admin/data/backups/${backupId}/download`, filename);
      toast.success("Backup downloaded successfully");
    } catch (error: any) {
      toast.error("Failed to download backup");
    }
  };

  return (
    <div className="w-full max-w-[1600px] mx-auto space-y-6">
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
              Download system data for offline analysis or external reporting.
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
              Permanently delete old reports and zones to free up database space.
            </p>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
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
              <Button
                variant="danger"
                className="w-full"
                disabled={!cleanupFrom || !cleanupTo}
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
            <Database className="w-5 h-5 text-indigo-600" />
            Database Backups
          </CardTitle>
          <Button onClick={handleCreateBackup} disabled={isLoading} className="bg-indigo-600 hover:bg-indigo-700">
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
            <div className="overflow-x-auto">
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
                      <td className="px-4 py-3 text-slate-600">{(backup.size_bytes / 1024).toFixed(1)} KB</td>
                      <td className="px-4 py-3 text-slate-600">{new Date(backup.created_at).toLocaleString()}</td>
                      <td className="px-4 py-3 text-right">
                        <TableActionGroup>
                          <TableActionButton
                            actionVariant="download"
                            onClick={() => downloadBackupFile(backup.id, backup.name)}
                          >
                            Download
                          </TableActionButton>
                          <TableActionButton
                            actionVariant="restore"
                            onClick={() => {
                              setRestoreId(backup.id);
                              setIsRestoreModalOpen(true);
                            }}
                          >
                            Restore
                          </TableActionButton>
                          <TableActionButton
                            actionVariant="delete"
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
          )}
        </CardContent>
      </Card>

      <ConfirmDialog
        isOpen={isRestoreModalOpen}
        title="Restore Database"
        message={
          <div className="space-y-2">
            <p>Are you sure you want to restore the database from this backup?</p>
            <div className="p-3 bg-amber-50 text-amber-800 rounded-md flex items-start gap-2">
              <ShieldAlert className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <p className="text-sm">
                <strong>WARNING:</strong> This action will overwrite the current database state.
                Any data created after this backup will be permanently lost.
              </p>
            </div>
          </div>
        }
        confirmLabel="Yes, Restore Database"
        cancelLabel="Cancel"
        onConfirm={handleRestore}
        onCancel={() => setIsRestoreModalOpen(false)}
        variant="destructive"
        isLoading={isLoading}
      />

      <ConfirmDialog
        isOpen={isCleanupModalOpen}
        title="Delete Data"
        message={
          <div className="space-y-2">
            <p>Are you sure you want to permanently delete data from <strong>{cleanupFrom}</strong> to <strong>{cleanupTo}</strong>?</p>
            <p className="text-sm text-slate-600">
              This will remove flood reports and avoidance zones in this date range. This action cannot be undone.
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

      <ConfirmDialog
        isOpen={isDeleteModalOpen}
        title="Delete Backup"
        message="Are you sure you want to permanently delete this database backup? This action cannot be undone."
        confirmLabel="Yes, Delete Backup"
        cancelLabel="Cancel"
        onConfirm={handleDeleteBackup}
        onCancel={() => setIsDeleteModalOpen(false)}
        variant="destructive"
        isLoading={isLoading}
      />
    </div>
  );
}
