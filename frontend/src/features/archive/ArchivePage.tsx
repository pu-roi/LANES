"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getReports, getUsers, FloodReport, UserRecord } from "@/features/admin/adminApi";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { DataTable, Column } from "@/shared/ui";
import {
  Loader2,
  Archive,
  Search,
  RefreshCw,
  AlertTriangle,
  FileText,
  Users
} from "lucide-react";

const LIMIT = 10;

export default function ArchivePage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"users" | "reports">("users");
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  const {
    data: usersData,
    isLoading: usersLoading,
    refetch: refetchUsers,
    isPlaceholderData: usersPlaceholder
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
    isPlaceholderData: reportsPlaceholder
  } = useQuery({
    queryKey: ["archivedReports", page, search],
    queryFn: () => getReports({ page, limit: LIMIT, search, archived: true }),
    enabled: activeTab === "reports",
    placeholderData: (prev) => prev,
  });

  const users = usersData?.users || [];
  const totalUsers = usersData?.total || 0;
  const usersTotalPages = Math.ceil(totalUsers / LIMIT);

  const reports = reportsData?.reports || [];
  const totalReports = reportsData?.total || 0;
  const reportsTotalPages = Math.ceil(totalReports / LIMIT);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
    setPage(1);
  };

  const handleTabChange = (tab: "users" | "reports") => {
    setActiveTab(tab);
    setPage(1);
    setSearch("");
  };

  const handleRefresh = () => {
    if (activeTab === "users") refetchUsers();
    else refetchReports();
  };

  const userColumns: Column<UserRecord>[] = [
    {
      key: 'id',
      title: 'User ID',
      sortable: true,
      className: 'whitespace-nowrap text-center',
      render: (user) => <span className="font-mono text-xs font-semibold">#{user.id}</span>
    },
    {
      key: 'username',
      title: 'Username',
      sortable: true,
      className: 'w-[200px]',
      render: (user) => <span className="font-semibold text-gray-800">{user.username}</span>
    },
    {
      key: 'email',
      title: 'Email',
      sortable: true,
      render: (user) => <span className="text-gray-600 font-medium">{user.email}</span>
    },
    {
      key: 'role',
      title: 'Role',
      sortable: true,
      className: 'whitespace-nowrap text-center',
      render: (user) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
          {user.role?.name || "Unknown"}
        </span>
      )
    },
    {
      key: 'deleted_at',
      title: 'Deleted At',
      sortable: false,
      className: 'whitespace-nowrap text-center',
      render: (user) => <span className="text-xs text-red-600 font-semibold">Deleted Record</span> // To be improved if deleted_at is added to UserRecord
    }
  ];

  const reportColumns: Column<FloodReport>[] = [
    {
      key: 'id',
      title: 'Report ID',
      sortable: true,
      className: 'whitespace-nowrap text-center',
      render: (report) => <span className="font-mono text-xs font-semibold">#{report.id}</span>
    },
    {
      key: 'severity',
      title: 'Severity',
      sortable: true,
      className: 'whitespace-nowrap text-center',
      render: (report) => (
        <span className="uppercase text-xs font-bold text-gray-500">
          {report.severity}
        </span>
      )
    },
    {
      key: 'raw_text',
      title: 'Description',
      sortable: false,
      render: (report) => (
        <div className="max-w-xs truncate text-sm text-gray-600">
          {report.raw_text || "No description provided."}
        </div>
      )
    },
    {
      key: 'deleted_at',
      title: 'Deleted At',
      sortable: false,
      className: 'whitespace-nowrap text-center',
      render: (report) => <span className="text-xs text-red-600 font-semibold">Deleted Record</span>
    }
  ];

  return (
    <div className="w-full max-w-[1600px] mx-auto space-y-6 text-gray-900">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight flex items-center gap-2">
            <Archive className="w-6 h-6 text-gray-500" />
            Archive Center
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Browse soft-deleted records for auditing and recovery purposes.
          </p>
        </div>
        <Button
          onClick={handleRefresh}
          variant="outline"
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </Button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex space-x-8">
          <button
            onClick={() => handleTabChange("users")}
            className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors ${
              activeTab === "users"
                ? "border-blue-600 text-blue-600 font-semibold"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            <Users className="w-4 h-4" />
            Archived Users
          </button>
          <button
            onClick={() => handleTabChange("reports")}
            className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors ${
              activeTab === "reports"
                ? "border-blue-600 text-blue-600 font-semibold"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            <FileText className="w-4 h-4" />
            Archived Reports
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
        <div className="flex flex-1 gap-3 w-full sm:w-auto">
          <Input
            containerClassName="flex-1 max-w-sm"
            leftIcon={<Search className="w-4 h-4 text-gray-400" />}
            type="text"
            placeholder={activeTab === "users" ? "Search users..." : "Search reports..."}
            value={search}
            onChange={handleSearchChange}
            className="text-gray-900 bg-white"
          />
        </div>

        <div className="text-xs font-semibold text-gray-400">
          Archived records found: <span className="text-gray-900">{activeTab === "users" ? totalUsers : totalReports}</span>
        </div>
      </div>

      {/* Table */}
      {(activeTab === "users" ? usersLoading : reportsLoading) ? (
        <div className="flex flex-col items-center justify-center py-20 bg-white border border-gray-200 rounded-xl shadow-sm">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-2" />
          <p className="text-sm text-gray-500">Loading archived records...</p>
        </div>
      ) : (
        <div className={`transition-opacity duration-150 ${(activeTab === "users" ? usersPlaceholder : reportsPlaceholder) ? "opacity-60" : "opacity-100"}`}>
          {activeTab === "users" ? (
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
                    No soft-deleted flood reports were found in the system.
                  </p>
                </div>
              }
            />
          )}
        </div>
      )}
    </div>
  );
}
