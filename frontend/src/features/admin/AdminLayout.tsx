"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import AdminSidebar from "@/features/navigation/AdminSidebar";
import LiveMapPage from "@/features/admin/LiveMapPage";
import { useAuth } from "@/hooks/useAuth";
import { Loader2 } from "lucide-react";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isLoading, isAuthenticated } = useAuth();
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isMounted || isLoading) return;

    if (!isAuthenticated || !user) {
      router.replace(`/login?redirect=${encodeURIComponent(pathname)}`);
      return;
    }

    const roleName = (user as any)?.role?.name;
    const isAdmin = roleName === "Super Admin" || roleName === "DRRM Officer" || roleName === "Moderator";
    if (!isAdmin) {
      router.replace("/map");
    }
  }, [isMounted, isLoading, isAuthenticated, user, router, pathname]);

  if (!isMounted || isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-100">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <p className="text-sm font-medium text-slate-600">Verifying credentials...</p>
        </div>
      </div>
    );
  }

  const roleName = (user as any)?.role?.name;
  const isAdmin = roleName === "Super Admin" || roleName === "DRRM Officer" || roleName === "Moderator";
  if (!isAuthenticated || !isAdmin) {
    return null;
  }

  const isMapPage = pathname === "/admin/map";

  return (
    <div className="flex h-screen bg-slate-100 overflow-hidden">
      <AdminSidebar />
      {/* Main Content Area */}
      <main className="flex-1 h-full overflow-hidden relative">
        {/* Persistent Spatial Operations Live Map View (never unmounts or reloads) */}
        <div
          className={`absolute inset-0 z-0 h-full w-full ${
            isMapPage ? "visible opacity-100 pointer-events-auto" : "invisible opacity-0 pointer-events-none"
          }`}
        >
          <LiveMapPage />
        </div>

        {/* Other Admin Sub-Pages (Dashboard, Reports, Settings, Users, etc.) */}
        {!isMapPage && (
          <div 
            data-lenis-prevent="true"
            className="relative z-10 h-full w-full p-6 overflow-y-auto bg-slate-100"
          >
            {children}
          </div>
        )}
      </main>
    </div>
  );
}
