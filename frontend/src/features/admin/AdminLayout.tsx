"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import AdminSidebar from "@/features/navigation/AdminSidebar";

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
      <main className={`flex-1 h-full overflow-hidden ${isMapPage ? "p-0" : "p-6 overflow-y-auto"}`}>
        {children}
      </main>
    </div>
  );
}
