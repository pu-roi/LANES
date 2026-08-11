"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getUsers, updateUserStatus, deleteUser, UserRecord, createAdminUser, updateUserRole, getRoles, RoleRecord } from "./adminApi";
import { Button } from "@/shared/ui/Button";
import { Modal } from "@/shared/ui/Modal";
import { Input } from "@/shared/ui/Input";
import { Select, TableActionGroup, TableActionButton, Pagination, DataTable, Column } from "@/shared/ui";
import {
  Loader2,
  Users,
  Search,
  Trash2,
  UserCheck,
  UserX,
  ChevronLeft,
  ChevronRight,
  Shield,
  RefreshCw,
  Info,
  AlertTriangle,
  Plus,
  Edit2
} from "lucide-react";

const LIMIT = 10;

export default function UsersPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("all");

  
  // Status toggle modals
  const [statusUser, setStatusUser] = useState<UserRecord | null>(null);
  // Delete modals
  const [deleteId, setDeleteId] = useState<number | null>(null);
  
  // Roles Query
  const { data: rolesData } = useQuery({
    queryKey: ["adminRoles"],
    queryFn: getRoles,
  });

  // Create User State
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [createUserForm, setCreateUserForm] = useState({ username: "", email: "", password: "", role_id: 4 });

  // Edit Role State
  const [editRoleUser, setEditRoleUser] = useState<UserRecord | null>(null);
  const [editRoleSelected, setEditRoleSelected] = useState<number>(4);

  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { data, isLoading, refetch, isPlaceholderData } = useQuery({
    queryKey: ["adminUsers", page, search, role],
    queryFn: () => getUsers(page, LIMIT, search, role),
    placeholderData: (prev) => prev,
    refetchInterval: 30000, // 30s background polling fallback
  });

  const toggleStatusMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) => 
      updateUserStatus(id, is_active),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminUsers"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
      setStatusUser(null);
      setErrorMessage(null);
    },
    onError: (err: any) => {
      setErrorMessage(err.message || "Failed to update user status");
    }
  });

  const removeUserMutation = useMutation({
    mutationFn: (id: number) => deleteUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminUsers"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
      setDeleteId(null);
      setErrorMessage(null);
    },
    onError: (err: any) => {
      setErrorMessage(err.message || "Failed to delete user account");
    }
  });

  const createUserMutation = useMutation({
    mutationFn: (data: any) => createAdminUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminUsers"] });
      queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
      setShowCreateUser(false);
      setCreateUserForm({ username: "", email: "", password: "", role_id: 4 });
      setErrorMessage(null);
    },
    onError: (err: any) => {
      setErrorMessage(err.message || "Failed to create user");
    }
  });

  const updateRoleMutation = useMutation({
    mutationFn: ({ id, role_id }: { id: number, role_id: number }) => updateUserRole(id, role_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminUsers"] });
      setEditRoleUser(null);
      setErrorMessage(null);
    },
    onError: (err: any) => {
      setErrorMessage(err.message || "Failed to update user role");
    }
  });

  const users = data?.users || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / LIMIT);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
    setPage(1);
  };

  const handleRoleTabChange = (newRole: string) => {
    setRole(newRole);
    setPage(1);
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
      className: 'whitespace-nowrap',
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
      sortFn: (a, b) => (a.role?.name || "Admin").localeCompare(b.role?.name || "Admin"),
      render: (user) => (
        user.role?.name !== "Commuter" ? (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-100">
            <Shield className="w-3 h-3" />
            {user.role?.name || "Admin"}
          </span>
        ) : (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
            Commuter
          </span>
        )
      )
    },
    {
      key: 'created_at',
      title: 'Created At',
      sortable: true,
      className: 'whitespace-nowrap text-center',
      render: (user) => <span className="text-xs">{new Date(user.created_at).toLocaleString()}</span>
    },
    {
      key: 'is_active',
      title: 'Status',
      sortable: true,
      className: 'whitespace-nowrap text-center',
      render: (user) => (
        user.is_active ? (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-100">
            Active
          </span>
        ) : (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-700 border border-red-100">
            Disabled
          </span>
        )
      )
    },
    {
      key: 'actions',
      title: 'Actions',
      sortable: false,
      className: 'whitespace-nowrap text-center',
      render: (user) => (
        <div className="flex justify-center">
          <TableActionGroup>
            <TableActionButton
              actionVariant="edit"
              onClick={() => {
                setEditRoleSelected(user.role_id);
                setEditRoleUser(user);
              }}
            >
              Change Role
            </TableActionButton>
            <TableActionButton
              actionVariant={user.is_active ? "disable" : "enable"}
              onClick={() => setStatusUser(user)}
            >
              {user.is_active ? "Disable" : "Enable"}
            </TableActionButton>
            <TableActionButton
              actionVariant="delete"
              onClick={() => setDeleteId(user.id)}
            >
              Delete
            </TableActionButton>
          </TableActionGroup>
        </div>
      )
    }
  ];

  return (
    <div className="w-full max-w-[1600px] mx-auto space-y-6 text-gray-900">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">User Registry</h1>
          <p className="text-gray-500 text-sm mt-1">
            Manage user accounts, roles, access statuses, and permissions.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => setShowCreateUser(true)}
            className="flex items-center gap-2 text-sm bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="w-4 h-4" />
            Create User
          </Button>
          <Button
            onClick={() => refetch()}
            variant="outline"
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Error Alert Banner */}
      {errorMessage && (
        <div className="flex items-start gap-3 p-4 bg-red-50 rounded-xl border border-red-200 text-red-800 text-sm">
          <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <h5 className="font-bold">Operation Refused</h5>
            <p className="mt-0.5">{errorMessage}</p>
          </div>
          <button 
            onClick={() => setErrorMessage(null)} 
            className="ml-auto font-bold hover:text-red-900"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex space-x-8">
          {[
            { id: "all", label: "All Accounts" },
            { id: "Commuter", label: "Citizens" },
            { id: "Sub-Administrator", label: "Sub-Administrators" },
            { id: "Super-Administrator", label: "Super-Administrators" }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleRoleTabChange(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                role === tab.id
                  ? "border-blue-600 text-blue-600 font-semibold"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
        <div className="flex flex-1 gap-3 w-full sm:w-auto">
          <Input
            containerClassName="flex-1 max-w-sm"
            leftIcon={<Search className="w-4 h-4 text-gray-400" />}
            type="text"
            placeholder="Search by username or email..."
            value={search}
            onChange={handleSearchChange}
            className="text-gray-900 bg-white"
          />
        </div>

        <div className="text-xs font-semibold text-gray-400">
          Matched accounts: <span className="text-gray-900">{total}</span>
        </div>
      </div>

      {/* User Records Table */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 bg-white border border-gray-200 rounded-xl shadow-sm">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-2" />
          <p className="text-sm text-gray-500">Loading user accounts...</p>
        </div>
      ) : (
        <div className={`transition-opacity duration-150 ${isPlaceholderData ? "opacity-60" : "opacity-100"}`}>
          <DataTable
            columns={userColumns}
            data={users}
            keyExtractor={(user) => user.id}
            pagination={{ page, totalPages, onPageChange: setPage }}
            emptyState={
              <div className="py-16 text-center">
                <Users className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900">No accounts matched</h3>
                <p className="text-gray-500 mt-1 max-w-sm mx-auto text-sm">
                  Try adjusting your search filters or check your spelling.
                </p>
              </div>
            }
          />
        </div>
      )}

      {/* Confirmation Modals */}
      <Modal
        isOpen={statusUser !== null}
        onClose={() => setStatusUser(null)}
        title="Toggle User Status"
      >
        <div className="space-y-4 text-sm text-gray-600">
          <div className="flex items-start gap-3 p-3 bg-amber-50 rounded-xl border border-amber-100 text-amber-800">
            <Info className="w-5 h-5 shrink-0 mt-0.5" />
            <p>
              {statusUser?.is_active 
                ? "Disabling this user will prevent them from logging in, accessing private navigation layers, or reporting flood hazards."
                : "Enabling this user will restore their full privileges to access their profile and submit hazards."}
            </p>
          </div>
          <p>
            Are you sure you want to {statusUser?.is_active ? "disable" : "enable"} user{" "}
            <strong>{statusUser?.username}</strong>?
          </p>
          <div className="flex justify-end gap-3 pt-2">
            <Button
              variant="outline"
              onClick={() => setStatusUser(null)}
              className="text-gray-600"
            >
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (statusUser) {
                  toggleStatusMutation.mutate({ 
                    id: statusUser.id, 
                    is_active: !statusUser.is_active 
                  });
                }
              }}
              disabled={toggleStatusMutation.isPending}
              className={`text-white ${
                statusUser?.is_active ? "bg-amber-500 hover:bg-amber-600" : "bg-emerald-600 hover:bg-emerald-700"
              }`}
            >
              {toggleStatusMutation.isPending ? "Updating..." : statusUser?.is_active ? "Disable Account" : "Enable Account"}
            </Button>
          </div>
        </div>
      </Modal>

      <Modal
        isOpen={deleteId !== null}
        onClose={() => setDeleteId(null)}
        title="Delete User Account"
      >
        <div className="space-y-4 text-sm text-gray-600">
          <div className="flex items-start gap-3 p-3 bg-red-50 rounded-xl border border-red-100 text-red-800">
            <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5 animate-pulse" />
            <p>
              Warning: Deleting this user is permanent. All profile details and access authorization records will be completely removed from the database.
            </p>
          </div>
          <p>Are you sure you want to permanently delete user <strong>#{deleteId}</strong>?</p>
          <div className="flex justify-end gap-3 pt-2">
            <Button
              variant="outline"
              onClick={() => setDeleteId(null)}
              className="text-gray-600"
            >
              Cancel
            </Button>
            <Button
              onClick={() => deleteId && removeUserMutation.mutate(deleteId)}
              disabled={removeUserMutation.isPending}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              {removeUserMutation.isPending ? "Deleting..." : "Permanently Delete"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Create User Modal */}
      <Modal
        isOpen={showCreateUser}
        onClose={() => setShowCreateUser(false)}
        title="Create New User"
      >
        <form 
          onSubmit={(e) => {
            e.preventDefault();
            createUserMutation.mutate(createUserForm);
          }}
          className="space-y-4"
        >
          <Input
            label="Username"
            value={createUserForm.username}
            onChange={(e) => setCreateUserForm({ ...createUserForm, username: e.target.value })}
            required
            className="bg-white text-gray-900"
            labelClassName="text-gray-900"
          />
          <Input
            label="Email"
            type="email"
            value={createUserForm.email}
            onChange={(e) => setCreateUserForm({ ...createUserForm, email: e.target.value })}
            required
            className="bg-white text-gray-900"
            labelClassName="text-gray-900"
          />
          <Input
            label="Password"
            type="password"
            value={createUserForm.password}
            onChange={(e) => setCreateUserForm({ ...createUserForm, password: e.target.value })}
            required
            className="bg-white text-gray-900"
            labelClassName="text-gray-900"
          />
          <div className="space-y-1.5">
            <label className="block text-sm font-semibold text-gray-900">Role</label>
            <Select
              options={rolesData?.map(role => ({ label: role.name, value: role.id })) || []}
              value={createUserForm.role_id}
              onChange={(e) => setCreateUserForm({ ...createUserForm, role_id: Number(e.target.value) })}
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="outline" onClick={() => setShowCreateUser(false)} className="text-gray-600">Cancel</Button>
            <Button type="submit" disabled={createUserMutation.isPending} className="bg-blue-600 hover:bg-blue-700 text-white">
              {createUserMutation.isPending ? "Creating..." : "Create User"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Role Modal */}
      <Modal
        isOpen={editRoleUser !== null}
        onClose={() => setEditRoleUser(null)}
        title="Change User Role"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Select a new role for <strong>{editRoleUser?.username}</strong>.
          </p>
          <div className="space-y-1.5">
            <label className="block text-sm font-semibold text-gray-900">Role</label>
            <Select
              options={rolesData?.map(role => ({ label: role.name, value: role.id })) || []}
              value={editRoleSelected}
              onChange={(e) => setEditRoleSelected(Number(e.target.value))}
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" onClick={() => setEditRoleUser(null)} className="text-gray-600">Cancel</Button>
            <Button 
              onClick={() => editRoleUser && updateRoleMutation.mutate({ id: editRoleUser.id, role_id: editRoleSelected })}
              disabled={updateRoleMutation.isPending}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {updateRoleMutation.isPending ? "Updating..." : "Save Role"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
