"use client";

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usePathname } from 'next/navigation';
import { Bell, Check, Info, MapPin, X } from 'lucide-react';
import { getNotifications, markAsRead, markAllAsRead, Notification } from './notificationsApi';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';

export function NotificationBell() {
  const { user, isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const pathname = usePathname();
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['notifications'],
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
  });

  const handleMarkRead = (id: number) => {
    markReadMutation.mutate(id);
  };

  const handleMarkAllRead = () => {
    markAllReadMutation.mutate();
  };

  const unreadCount = data?.unread_count || 0;

  // Do not show on map page
  if (pathname === '/map') {
    return null;
  }

  const getIcon = (type: string) => {
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
    <div 
      className={cn(
        "fixed right-6 z-50",
        isPostDetail ? "hidden sm:block" : "block",
        "bottom-[calc(var(--bottom-nav-height)+1rem)] sm:bottom-6"
      )}
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative bg-white p-3 rounded-full shadow-[0_0_20px_rgba(59,130,246,0.5)] ring-4 ring-blue-400/30 border border-blue-200 hover:bg-blue-50 hover:shadow-[0_0_30px_rgba(59,130,246,0.7)] hover:ring-blue-400/50 transition-all duration-300 focus:outline-none"
        aria-label="Notifications"
      >
        <Bell size={24} className="text-gray-700" />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 border-2 border-white rounded-full">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute bottom-16 right-0 w-80 sm:w-96 bg-white rounded-xl shadow-2xl border border-gray-100 overflow-hidden flex flex-col max-h-[60vh]">
          <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
            <h3 className="font-bold text-gray-900">Notifications</h3>
            <div className="flex gap-3">
              {unreadCount > 0 && (
                <button 
                  onClick={handleMarkAllRead}
                  className="text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors"
                >
                  Mark all as read
                </button>
              )}
              <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X size={16} />
              </button>
            </div>
          </div>

          <div className="overflow-y-auto flex-1">
            {!isAuthenticated ? (
              <div className="p-8 text-center text-gray-500 text-sm flex flex-col items-center gap-2">
                <Bell size={24} className="text-gray-300" />
                <p>Sign in to view your notifications.</p>
              </div>
            ) : isLoading || isAuthLoading ? (
              <div className="p-8 text-center text-gray-500 text-sm">Loading notifications...</div>
            ) : !data || data.notifications.length === 0 ? (
              <div className="p-8 text-center text-gray-500 text-sm flex flex-col items-center gap-2">
                <Bell size={24} className="text-gray-300" />
                <p>You're all caught up!</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-50">
                {data.notifications.map((notif: Notification) => (
                  <div 
                    key={notif.id} 
                    className={`p-4 flex gap-3 hover:bg-gray-50 transition-colors ${!notif.is_read ? 'bg-blue-50/30' : ''}`}
                    onClick={() => {
                      if (!notif.is_read) handleMarkRead(notif.id);
                    }}
                  >
                    <div className="shrink-0">
                      {getIcon(notif.type)}
                    </div>
                    <div className="flex-1 min-w-0">
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
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
