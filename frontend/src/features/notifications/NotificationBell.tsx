"use client";

import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usePathname, useRouter } from 'next/navigation';
import { Bell, Check, Info, MapPin, X, AlertTriangle, Clock, XCircle } from 'lucide-react';
import { getNotifications, getNotificationReport, markAsRead, markAllAsRead, Notification } from './notificationsApi';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';
import { Button, FloodReportDetailsModal } from "@/shared/ui";
import type { FloodReportDetails } from '@/shared/ui/feedback/FloodReportDetailsModal';

const referenceId = (value: unknown): number | null =>
  typeof value === 'number' && Number.isSafeInteger(value) && value > 0 ? value : null;

const notificationTitle = (notification: Notification): string | null => {
  if (typeof notification.payload?.title === 'string') return notification.payload.title;
  switch (notification.payload?.action) {
    case 'flood_report_under_review': return 'Flood Report Under Review';
    case 'flood_report_approved': return 'Flood Report Approved';
    case 'flood_report_rejected': return 'Flood Report Rejected';
    case 'warn': return Array.isArray(notification.payload?.reasons) ? 'Post Moderation Warning' : null;
    default: return null;
  }
};

export function NotificationBell() {
  const { user, isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [openingId, setOpeningId] = useState<number | null>(null);
  const [reportDetail, setReportDetail] = useState<{ ownerId: number; report: FloodReportDetails } | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['notifications', user?.id],
    queryFn: () => getNotifications(0, 20),
    refetchInterval: 60000, // Poll every minute
    enabled: isAuthenticated && pathname !== '/map', // Only fetch if logged in and not on map
  });

  const markReadMutation = useMutation({
    mutationFn: markAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: markAllAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
    onError: () => setActionError('Could not mark notifications as read. Please try again.'),
  });

  const openNotification = async (notification: Notification) => {
    setActionError(null);
    setOpeningId(notification.id);
    try {
      if (!notification.is_read) await markReadMutation.mutateAsync(notification.id);
      const reportId = referenceId(notification.payload?.report_id);
      const postId = referenceId(notification.payload?.post_id);
      if (reportId !== null) {
        const report = await getNotificationReport(reportId);
        if (report.id !== reportId) throw new Error('The requested flood report is unavailable.');
        setReportDetail({ ownerId: notification.user_id, report });
        setIsOpen(false);
      } else if (postId !== null) {
        router.push(`/feed/${postId}`);
        setIsOpen(false);
      }
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Could not open this notification. Please try again.');
    } finally {
      setOpeningId(null);
    }
  };

  const handleMarkAllRead = () => {
    setActionError(null);
    markAllReadMutation.mutate();
  };

  const unreadCount = isAuthenticated ? data?.unread_count || 0 : 0;

  // Do not show on map page
  if (pathname === '/map') {
    return null;
  }

  const getIcon = (type: string, message: string = "", action: unknown = null) => {
    if (action === 'flood_report_under_review') return <div className="p-2 bg-blue-100 text-blue-600 rounded-full"><Clock size={16} /></div>;
    if (action === 'flood_report_approved') return <div className="p-2 bg-green-100 text-green-600 rounded-full"><Check size={16} /></div>;
    if (action === 'flood_report_rejected') return <div className="p-2 bg-rose-100 text-rose-600 rounded-full"><XCircle size={16} /></div>;
    const isWarningOrRemoval = message.toLowerCase().includes("removed") || 
      message.toLowerCase().includes("hid") || 
      message.toLowerCase().includes("warn");

    if (isWarningOrRemoval) {
      return <div className="p-2 bg-amber-100 text-amber-700 rounded-full"><AlertTriangle size={16} /></div>;
    }

    switch (type.toUpperCase()) {
      case 'LIKE':
        return <div className="p-2 bg-blue-100 text-blue-600 rounded-full"><Check size={16} /></div>;
      case 'COMMENT':
        return <div className="p-2 bg-green-100 text-green-600 rounded-full"><Info size={16} /></div>;
      case 'SYSTEM':
      default:
        return <div className="p-2 bg-gray-100 text-gray-600 rounded-full"><MapPin size={16} /></div>;
    }
  };

  // Hide on map page or admin pages
  if (pathname === '/map' || pathname.startsWith('/admin')) {
    return null;
  }

  // Hide on post detail page on mobile
  const isPostDetail = /^\/feed\/\d+$/.test(pathname);

  return (
    <><div
      id="notification-bell"
      className={cn(
        "fixed right-6 z-50",
        isPostDetail ? "hidden sm:block" : "block",
        "bottom-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom)+1rem)] sm:bottom-6"
      )}
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative bg-white p-3 rounded-full shadow-[0_0_20px_rgba(59,130,246,0.5)] ring-4 ring-blue-400/30 border border-blue-200 hover:bg-blue-50 hover:shadow-[0_0_30px_rgba(59,130,246,0.7)] hover:ring-blue-400/50 transition-all duration-300 focus:outline-none"
        aria-label="Notifications"
        aria-expanded={isOpen}
      >
        <Bell size={24} className="text-gray-700" />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 border-2 border-white rounded-full">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute bottom-16 right-0 w-80 max-w-[calc(100vw-3rem)] sm:w-96 bg-white rounded-xl shadow-2xl border border-gray-100 overflow-hidden flex flex-col max-h-[60vh]">
          <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
            <h3 className="font-bold text-gray-900">Notifications</h3>
            <div className="flex gap-3">
              {unreadCount > 0 && (
                <Button 
                  variant="ghost"
                  size="sm"
                  onClick={handleMarkAllRead}
                  disabled={markAllReadMutation.isPending || openingId !== null}
                  className="text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors"
                >
                  Mark all as read
                </Button>
              )}
              <Button variant="ghost" size="sm" aria-label="Close notifications" onClick={() => setIsOpen(false)} className="h-8 w-8 px-2 text-slate-500">
                <X size={16} />
              </Button>
            </div>
          </div>

          <div data-lenis-prevent className="overflow-y-auto flex-1">
            {isAuthenticated && (actionError || isError) && <div className="p-4 text-sm text-red-700" role="alert">
              {actionError || 'Could not load notifications. Please try again.'}
              {isError && <Button variant="ghost" size="sm" onClick={() => void refetch()}>Retry</Button>}
            </div>}
            {openingId !== null && <p className="px-4 py-2 text-sm text-slate-500" role="status">Opening notification...</p>}
            {!isAuthenticated ? (
              <div className="p-8 text-center text-gray-500 text-sm flex flex-col items-center gap-2">
                <Bell size={24} className="text-gray-300" />
                <p>Sign in to view your notifications.</p>
              </div>
            ) : isLoading || isAuthLoading ? (
              <div className="p-8 text-center text-gray-500 text-sm">Loading notifications...</div>
            ) : isError && !data ? null : !data || data.notifications.length === 0 ? (
              <div className="p-8 text-center text-gray-500 text-sm flex flex-col items-center gap-2">
                <Bell size={24} className="text-gray-300" />
                <p>You&apos;re all caught up!</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-50">
                {data.notifications.map((notif: Notification) => (
                  <Button variant="ghost"
                    key={notif.id} 
                    className={`h-auto w-full justify-start rounded-none p-4 flex gap-3 whitespace-normal text-left hover:bg-gray-50 transition-colors ${!notif.is_read ? 'bg-blue-50/30' : ''}`}
                    disabled={openingId !== null || markAllReadMutation.isPending}
                    onClick={() => void openNotification(notif)}
                  >
                    <div className="shrink-0">
                      {getIcon(notif.type, notif.message, notif.payload?.action)}
                    </div>
                    <div className="flex-1 min-w-0">
                      {notificationTitle(notif) && <p className="mb-1 text-sm font-bold text-gray-900">{notificationTitle(notif)}</p>}
                      <p className={`text-sm text-gray-800 ${!notif.is_read ? 'font-semibold' : ''}`}>
                        {notif.message}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(notif.created_at).toLocaleString(undefined, { 
                          month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' 
                        })}
                      </p>
                    </div>
                    {!notif.is_read && (
                      <div className="shrink-0 flex items-center">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      </div>
                    )}
                  </Button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>{reportDetail && createPortal(<div className="relative z-[100]"><FloodReportDetailsModal
      isOpen={Boolean(isAuthenticated && reportDetail && reportDetail.ownerId === user?.id)}
      report={isAuthenticated && reportDetail && reportDetail.ownerId === user?.id ? reportDetail.report : null}
      onClose={() => setReportDetail(null)}
    /></div>, document.body)}</>
  );
}
