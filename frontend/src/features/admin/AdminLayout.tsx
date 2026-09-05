"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import AdminSidebar from "@/features/navigation/AdminSidebar";
import LiveMapPage from "@/features/admin/LiveMapPage";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    const token = localStorage.getItem("lanes_token");
    if (!token) {
      router.push("/login");
    }
  }, [router]);

  if (!isMounted) return null; // Prevent hydration errors

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
