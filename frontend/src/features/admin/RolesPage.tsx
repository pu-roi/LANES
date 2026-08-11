"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getRoles, createRole, updateRole, deleteRole, cloneRole, RoleRecord, RoleCreate, RoleUpdate } from "./adminApi";
import { Button } from "@/shared/ui/Button";
import { Modal } from "@/shared/ui/Modal";
import { Input } from "@/shared/ui/Input";
import { Select } from "@/shared/ui";
import { useToast } from "@/shared/ui";
import {
  Loader2,
  Shield,
  Trash2,
  Copy,
  Edit2,
  AlertTriangle,
  RefreshCw,
  Plus
} from "lucide-react";

export default function RolesPage() {
  const queryClient = useQueryClient();
  const { success, error } = useToast();
  
  // Modals state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editRole, setEditRole] = useState<RoleRecord | null>(null);
  const [cloneRoleItem, setCloneRoleItem] = useState<RoleRecord | null>(null);
  const [deleteRoleItem, setDeleteRoleItem] = useState<RoleRecord | null>(null);
  
  // Form state
  const [name, setName] = useState("");
  const [permissions, setPermissions] = useState<Record<string, string>>({
    reports: "none",
    zones: "none",
    users: "none",
    roles: "none",
    audit: "none",
    data: "none",
    settings: "none",
  });

  const { data: roles, isLoading, refetch } = useQuery({
    queryKey: ["adminRoles"],
    queryFn: getRoles,
  });

  const createMutation = useMutation({
    mutationFn: (data: RoleCreate) => createRole(data),
    onSuccess: () => {
      success("Role Created", `The role "${name}" has been created.`);
      queryClient.invalidateQueries({ queryKey: ["adminRoles"] });
      closeModals();
    },
    onError: (err: any) => {
      error("Operation Failed", err.message || "Failed to create role");
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: RoleUpdate }) => updateRole(id, data),
    onSuccess: () => {
      success("Role Updated", `The permissions have been updated.`);
      queryClient.invalidateQueries({ queryKey: ["adminRoles"] });
      closeModals();
    },
    onError: (err: any) => {
      error("Operation Failed", err.message || "Failed to update role");
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteRole(id),
    onSuccess: () => {
      success("Role Deleted", `The role has been permanently deleted.`);
      queryClient.invalidateQueries({ queryKey: ["adminRoles"] });
      closeModals();
    },
    onError: (err: any) => {
      error("Operation Failed", err.message || "Failed to delete role");
    }
  });

  const cloneMutation = useMutation({
    mutationFn: ({ id, newName }: { id: number; newName: string }) => cloneRole(id, newName),
    onSuccess: () => {
      success("Role Cloned", `The role has been cloned to "${name}".`);
      queryClient.invalidateQueries({ queryKey: ["adminRoles"] });
      closeModals();
    },
    onError: (err: any) => {
      error("Operation Failed", err.message || "Failed to clone role");
    }
  });

  const closeModals = () => {
    setIsCreateModalOpen(false);
    setEditRole(null);
    setCloneRoleItem(null);
    setDeleteRoleItem(null);
    setName("");
    setPermissions({
      reports: "none", zones: "none", users: "none", roles: "none", audit: "none", data: "none", settings: "none",
    });
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({ name, permissions });
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editRole) {
      updateMutation.mutate({ id: editRole.id, data: { name, permissions } });
    }
  };

  const handleCloneSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (cloneRoleItem) {
      cloneMutation.mutate({ id: cloneRoleItem.id, newName: name });
    }
  };

  const sections = ["reports", "zones", "users", "roles", "audit", "data", "settings"];

  return (
    <div className="w-full max-w-[1600px] mx-auto space-y-6 text-gray-900">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Role Management</h1>
          <p className="text-gray-500 text-sm mt-1">
            Configure dynamic roles and Role-Based Access Control (RBAC) permissions.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => refetch()}
            variant="outline"
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
          <Button
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center gap-2 text-sm bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plus className="w-4 h-4" />
            Create Role
          </Button>
        </div>
      </div>

      {/* Roles Grid */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 bg-white border border-gray-200 rounded-xl shadow-sm">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-2" />
          <p className="text-sm text-gray-500">Loading roles...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {roles?.map((role) => (
            <div key={role.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm flex flex-col">
              <div className="p-5 border-b border-gray-100 flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-gray-900 flex items-center gap-2">
                    <Shield className="w-4 h-4 text-blue-600" />
                    {role.name}
                  </h3>
                  {role.is_template && (
                    <span className="inline-block mt-1 px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 text-gray-500 uppercase tracking-wider">
                      Template
                    </span>
                  )}
                </div>
              </div>
              
              <div className="p-5 flex-1 text-sm text-gray-600">
                <div className="grid grid-cols-2 gap-y-2 gap-x-4">
                  {sections.map((sec) => (
                    <div key={sec} className="flex justify-between">
                      <span className="capitalize">{sec}:</span>
                      <span className="font-semibold text-gray-900 capitalize">
                        {role.permissions[sec] || "None"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-3 bg-gray-50 border-t border-gray-100 flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setCloneRoleItem(role);
                    setName(role.name + " (Copy)");
                  }}
                  className="text-xs px-2.5 py-1.5 h-auto text-blue-600 border-blue-100 hover:bg-blue-50"
                  title="Clone Role"
                >
                  <Copy className="w-3.5 h-3.5" />
                </Button>
                
                {!role.is_template && (
                  <>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setEditRole(role);
                        setName(role.name);
                        setPermissions(role.permissions as any);
                      }}
                      className="text-xs px-2.5 py-1.5 h-auto text-amber-600 border-amber-100 hover:bg-amber-50"
                      title="Edit Role"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => setDeleteRoleItem(role)}
                      className="text-xs px-2.5 py-1.5 h-auto text-red-600 border-red-100 hover:bg-red-50"
                      title="Delete Role"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Modal */}
      <Modal
        isOpen={isCreateModalOpen || !!editRole}
        onClose={closeModals}
        title={editRole ? "Edit Role" : "Create Custom Role"}
      >
        <form onSubmit={editRole ? handleEditSubmit : handleCreateSubmit} className="space-y-4">
          <Input
            label="Role Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Guest Moderator"
            required
          />
          
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Permissions</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {sections.map((sec) => (
                <div key={sec} className="flex items-center bg-gray-50 p-2 rounded border border-gray-200 gap-2">
                  <span className="text-sm font-medium capitalize text-gray-700 w-16">{sec}</span>
                  <Select
                    value={permissions[sec] || "none"}
                    onChange={(e) => setPermissions({ ...permissions, [sec]: String(e.target.value) })}
                    className="flex-1"
                    options={[
                      { label: "None", value: "none" },
                      { label: "View", value: "view" },
                      { label: "Edit", value: "edit" },
                      { label: "Full", value: "full" },
                    ]}
                  />
                </div>
              ))}
            </div>
          </div>
          
          <div className="pt-4 flex justify-end gap-3 border-t border-gray-100">
            <Button type="button" variant="outline" onClick={closeModals}>Cancel</Button>
            <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending} className="bg-blue-600 hover:bg-blue-700 text-white">
              {createMutation.isPending || updateMutation.isPending ? "Saving..." : "Save Role"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Clone Modal */}
      <Modal
        isOpen={!!cloneRoleItem}
        onClose={closeModals}
        title="Clone Role"
      >
        <form onSubmit={handleCloneSubmit} className="space-y-4">
          <p className="text-sm text-gray-600">
            Create a new role with identical permissions to <strong>{cloneRoleItem?.name}</strong>.
          </p>
          <Input
            label="New Role Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter cloned role name"
            required
          />
          <div className="pt-4 flex justify-end gap-3 border-t border-gray-100">
            <Button type="button" variant="outline" onClick={closeModals}>Cancel</Button>
            <Button type="submit" disabled={cloneMutation.isPending} className="bg-blue-600 hover:bg-blue-700 text-white">
              {cloneMutation.isPending ? "Cloning..." : "Clone Role"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Modal */}
      <Modal
        isOpen={!!deleteRoleItem}
        onClose={closeModals}
        title="Delete Role"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Are you sure you want to permanently delete the role <strong>{deleteRoleItem?.name}</strong>?
            Any users currently assigned to this role must be reassigned first.
          </p>
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
            <Button variant="outline" onClick={closeModals}>Cancel</Button>
            <Button 
              onClick={() => deleteRoleItem && deleteMutation.mutate(deleteRoleItem.id)}
              disabled={deleteMutation.isPending}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              {deleteMutation.isPending ? "Deleting..." : "Yes, Delete"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
