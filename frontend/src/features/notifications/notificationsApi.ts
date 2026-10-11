import { apiClient } from '@/lib/apiClient';
import type { FloodReportDetails } from '@/shared/ui/feedback/FloodReportDetailsModal';

export interface Notification {
  id: number;
  user_id: number;
  type: string;
  message: string;
  payload: Record<string, unknown> | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationPaginatedResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
  has_more: boolean;
}

export const getNotifications = async (skip: number = 0, limit: number = 50): Promise<NotificationPaginatedResponse> => {
  return await apiClient.get<NotificationPaginatedResponse>(`/notifications?skip=${skip}&limit=${limit}`);
};

export const markAsRead = async (notificationId: number): Promise<Notification> => {
  return await apiClient.post<Notification>(`/notifications/${notificationId}/read`);
};

export const markAllAsRead = async (): Promise<{ message: string }> => {
  return await apiClient.post<{ message: string }>(`/notifications/read-all`);
};

export const getNotificationReport = (reportId: number): Promise<FloodReportDetails> =>
  apiClient.get<FloodReportDetails>(`/reports/me/${reportId}`);
