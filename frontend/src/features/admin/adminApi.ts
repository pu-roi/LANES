import { apiClient } from "@/lib/apiClient";

export interface PointGeometry {
  type: "Point";
  coordinates: [number, number];
}

export interface LineStringGeometry {
  type: "LineString";
  coordinates: [number, number][];
}

export type ReportGeometry = PointGeometry | LineStringGeometry;

/** Geometry drawn by admin in ZoneGeometryEditor */
export type DrawnGeometry = PolygonGeometry | LineStringGeometry;

export interface ReportSurvey {
  id?: number;
  report_id?: number;
  passable_vehicles?: string | null;
  hidden_hazards?: "yes" | "no" | "unsure" | string;
}

export interface FloodReport {
  id: number;
  source: string;
  raw_text: string;
  severity: "low" | "medium" | "high" | "extreme";
  depth?: string;
  geometry: ReportGeometry | null;
  media_urls?: string[];
  status: "pending" | "approved" | "rejected";
  zone_id?: number | null;
  barangay?: string | null;
  human_readable_location?: string | null;
  user_id?: number | null;
  created_at: string;
  updated_at: string;
  approved_at?: string | null;
  survey?: ReportSurvey | null;
  reporter_name?: string | null;
  reporter_username?: string | null;
  reporter_role?: string | null;
  reporter_trust_score?: number | null;
}

export interface ApproveReportPayload {
  action?: "CREATE_NEW" | "MERGE";
  target_zone_id?: number;
  custom_geometry?: PolygonGeometry;
  buffer_radius?: number;
  severity?: string;
  depth?: string;
}

export interface NearbyZone {
  id: number;
  severity: string;
  depth?: string | null;
  distance_meters: number;
  created_at: string;
  geometry: PolygonGeometry;
  report_count: number;
}

export interface PaginatedReportsResponse {
  reports: FloodReport[];
  total: number;
}

export interface DashboardStats {
  total_pending_reports: number;
  total_active_zones: number;
  total_approved_today: number;
  total_rejected_today: number;
  total_users: number;
  database_status: string;
}

export interface GetReportsOptions {
  page: number;
  limit: number;
  status?: string;
  severity?: string;
  search?: string;
  sortBy?: string;
  archived?: boolean;
  date_from?: string;
  date_to?: string;
  barangays?: string[];
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return apiClient.get<DashboardStats>("/admin/dashboard/stats");
}

export async function getReports(options: GetReportsOptions): Promise<PaginatedReportsResponse> {
  const skip = (options.page - 1) * options.limit;
  const params = new URLSearchParams();
  params.append("skip", skip.toString());
  params.append("limit", options.limit.toString());
  
  if (options.status && options.status !== "all") {
    params.append("status", options.status);
  }
  if (options.severity && options.severity !== "all") {
    params.append("severity", options.severity);
  }
  if (options.search) {
    params.append("search", options.search);
  }
  if (options.sortBy) {
    params.append("sort_by", options.sortBy);
  }
  if (options.archived) {
    params.append("archived", "true");
  }
  if (options.date_from) {
    params.append("date_from", options.date_from);
  }
  if (options.date_to) {
    params.append("date_to", options.date_to);
  }
  if (options.barangays && options.barangays.length > 0) {
    params.append("barangays", options.barangays.join(","));
  }

  return apiClient.get<PaginatedReportsResponse>(`/admin/reports/all?${params.toString()}`);
}

export async function approveReport(reportId: number, payload?: ApproveReportPayload): Promise<FloodReport> {
  return apiClient.post<FloodReport>(`/admin/reports/${reportId}/approve`, payload || { action: "CREATE_NEW" });
}

export async function rejectReport(reportId: number): Promise<FloodReport> {
  return apiClient.post<FloodReport>(`/admin/reports/${reportId}/reject`, {});
}

export async function getNearbyZones(reportId: number, maxDistanceMeters: number = 400): Promise<NearbyZone[]> {
  return apiClient.get<NearbyZone[]>(`/admin/zones/nearby?report_id=${reportId}&max_distance_meters=${maxDistanceMeters}`);
}

export async function getPendingReports(): Promise<FloodReport[]> {
  return apiClient.get<FloodReport[]>("/admin/reports/pending");
}

/**
 * Fetches other pending reports that share the same street/location segment as
 * the given report, suitable for batch street merge.
 */
export async function getReportsByLocation(reportId: number): Promise<FloodReport[]> {
  try {
    return apiClient.get<FloodReport[]>(`/admin/reports/by-location?report_id=${reportId}`);
  } catch {
    // Endpoint may not yet exist; return empty array gracefully
    return [];
  }
}

export interface PolygonGeometry {
  type: "Polygon";
  coordinates: [number, number][][];
}

export interface ZoneContributor {
  report_id: number;
  reporter_name: string;
  reporter_username?: string;
  reporter_role?: string;
  reporter_trust_score: number;
  raw_text: string;
  severity: string;
  depth?: string;
  created_at: string;
  is_primary: boolean;
  geometry?: ReportGeometry | null;
}

export interface AvoidanceZone {
  id: number;
  report_id: number;
  geometry: PolygonGeometry;
  is_active: boolean;
  created_at: string;
  expires_at: string | null;
  severity: string;
  depth?: string;
  report_text?: string;
  report_source?: string;
  reporter_name?: string;
  reporter_trust_score?: number;
  reporter_reports_submitted?: number;
  reporter_reports_verified?: number;
  contributors?: ZoneContributor[];
}

export interface PaginatedZonesResponse {
  zones: AvoidanceZone[];
  total: number;
}

export async function getZones(page: number, limit: number, activeOnly: boolean = false): Promise<PaginatedZonesResponse> {
  const skip = (page - 1) * limit;
  return apiClient.get<PaginatedZonesResponse>(`/admin/zones/all?skip=${skip}&limit=${limit}&active_only=${activeOnly}`);
}

export async function deactivateZone(zoneId: number): Promise<AvoidanceZone> {
  return apiClient.request<AvoidanceZone>(`/admin/zones/${zoneId}/deactivate`, { method: "PATCH" });
}

export async function deactivateZonesBulk(zoneIds: number[]): Promise<{ message: string; count: number }> {
  return apiClient.post<{ message: string; count: number }>("/admin/zones/deactivate-bulk", { zone_ids: zoneIds });
}

export interface UserRecord {
  id: number;
  username: string;
  email: string;
  role_id: number;
  role: RoleRecord;
  is_active: boolean;
  created_at: string;
}

export interface PaginatedUsersResponse {
  users: UserRecord[];
  total: number;
}

export async function getUsers(
  page: number,
  limit: number,
  search?: string,
  role?: string,
  archived?: boolean
): Promise<PaginatedUsersResponse> {
  const skip = (page - 1) * limit;
  const params = new URLSearchParams();
  params.append("skip", skip.toString());
  params.append("limit", limit.toString());
  if (search) params.append("search", search);
  if (role && role !== "all") params.append("role", role);
  if (archived) params.append("archived", "true");
  
  return apiClient.get<PaginatedUsersResponse>(`/admin/users?${params.toString()}`);
}

export async function updateUserStatus(userId: number, isActive: boolean): Promise<UserRecord> {
  return apiClient.request<UserRecord>(`/admin/users/${userId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ is_active: isActive }),
  });
}

export async function updateUserRole(userId: number, roleId: number): Promise<UserRecord> {
  return apiClient.request<UserRecord>(`/admin/users/${userId}/role`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role_id: roleId }),
  });
}

export async function createAdminUser(data: any): Promise<UserRecord> {
  return apiClient.post<UserRecord>("/admin/users", data);
}

export async function deleteUser(userId: number): Promise<{ message: string }> {
  return apiClient.request<{ message: string }>(`/admin/users/${userId}`, { method: "DELETE" });
}

export interface AuditLogRecord {
  id: number;
  admin_id: number | null;
  action_type: string;
  target_table: string;
  target_id: number | null;
  metadata_json: any | null;
  ip_address: string | null;
  created_at: string;
  admin?: {
    id: number;
    username: string;
    email: string;
    role: string;
  } | null;
}

export interface PaginatedAuditLogsResponse {
  logs: AuditLogRecord[];
  total: number;
}

export async function getAuditLogs(
  page: number,
  limit: number,
  actionType?: string,
  adminId?: number
): Promise<PaginatedAuditLogsResponse> {
  const skip = (page - 1) * limit;
  const params = new URLSearchParams();
  params.append("skip", skip.toString());
  params.append("limit", limit.toString());
  if (actionType && actionType !== "all") params.append("action_type", actionType);
  if (adminId) params.append("admin_id", adminId.toString());

  return apiClient.get<PaginatedAuditLogsResponse>(`/admin/audit-logs?${params.toString()}`);
}
export interface RoleRecord {
  id: number;
  name: string;
  permissions: Record<string, string>;
  is_template: boolean;
  created_at: string;
}

export interface RoleCreate {
  name: string;
  permissions: Record<string, string>;
}

export interface RoleUpdate {
  name?: string;
  permissions?: Record<string, string>;
}

export async function getRoles(): Promise<RoleRecord[]> {
  return apiClient.get<RoleRecord[]>('/admin/roles');
}

export async function createRole(data: RoleCreate): Promise<RoleRecord> {
  return apiClient.post<RoleRecord>('/admin/roles', data);
}

export async function updateRole(id: number, data: RoleUpdate): Promise<RoleRecord> {
  return apiClient.put<RoleRecord>(`/admin/roles/${id}`, data);
}

export async function deleteRole(id: number): Promise<void> {
  return apiClient.delete(`/admin/roles/${id}`);
}

export async function cloneRole(id: number, new_name: string): Promise<RoleRecord> {
  return apiClient.post<RoleRecord>(`/admin/roles/${id}/clone?new_name=${encodeURIComponent(new_name)}`);
}

export interface BackupFile {
  id: string;
  name: string;
  size_bytes: number;
  created_at: string;
  created_by: string | null;
}

export async function getBackups(): Promise<BackupFile[]> {
  return apiClient.get<BackupFile[]>('/admin/data/backups');
}

export async function createBackup(): Promise<BackupFile> {
  return apiClient.post<BackupFile>('/admin/data/backup', {});
}

export async function restoreBackup(backupId: string, confirm: boolean): Promise<{ detail: string }> {
  return apiClient.post<{ detail: string }>(`/admin/data/restore/${backupId}`, { confirm });
}

export async function deleteBackup(backupId: string): Promise<{ detail: string }> {
  return apiClient.request<{ detail: string }>(`/admin/data/backups/${backupId}`, { method: "DELETE" });
}

export async function cleanupData(dateFrom: string, dateTo: string, confirm: boolean): Promise<{ detail: string }> {
  return apiClient.request<{ detail: string }>('/admin/data/cleanup', {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ date_from: dateFrom, date_to: dateTo, confirm }),
  });
}

export type SystemSettings = Record<string, any>;

export async function getSettings(): Promise<SystemSettings> {
  return apiClient.get<SystemSettings>('/admin/settings');
}

export async function updateSettings(settings: SystemSettings): Promise<SystemSettings> {
  return apiClient.put<SystemSettings>('/admin/settings', { settings });
}

export interface DashboardChartsData {
  severity_distribution: Record<string, number>;
  reports_timeline: { date: string; count: number }[];
  top_barangays: { barangay: string; count: number }[];
}

export async function getDashboardCharts(): Promise<DashboardChartsData> {
  return apiClient.get<DashboardChartsData>('/admin/dashboard/charts');
}

export async function updateZoneExpiration(zoneId: number, expiresAt: string | null): Promise<AvoidanceZone> {
  return apiClient.request<AvoidanceZone>(`/admin/zones/${zoneId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ expires_at: expiresAt }),
  });
}

export interface MergePendingResponse {
  message: string;
  merged_count: number;
  zone_id: number;
}

/**
 * Batch-approve a list of pending reports and merge them all into an existing zone.
 * Each reporter is credited +5 Trust Score.
 */
export async function mergePendingIntoZone(
  zoneId: number,
  reportIds: number[]
): Promise<MergePendingResponse> {
  return apiClient.post<MergePendingResponse>(
    `/admin/zones/${zoneId}/merge-pending`,
    { report_ids: reportIds }
  );
}
