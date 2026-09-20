"use client";

import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import { Logo } from "@/shared/ui";
import {
  LayoutDashboard,
  Map,
  Users,
  ShieldCheck,
  ClipboardList,
  Flag,
  Archive,
  Database,
  Settings,
  LogOut,
  Home
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/shared/ui";
import { useSidebarStore } from "@/shared/stores/sidebarStore";

const navItems = [
  { name: "Dashboard",          href: "/admin/dashboard", icon: LayoutDashboard },
  { name: "Spatial Operations", href: "/admin/map",       icon: Map },
  { name: "User Registry",      href: "/admin/users",     icon: Users },
  { name: "Roles",              href: "/admin/roles",     icon: ShieldCheck },
  { name: "Audit Trail",        href: "/admin/audit",     icon: ClipboardList },
  { name: "Moderation Center",  href: "/admin/moderation",icon: Flag },
  { name: "Archive Center",     href: "/admin/archive",   icon: Archive },
  { name: "Data Management",    href: "/admin/data",      icon: Database },
  { name: "System Settings",    href: "/admin/settings",  icon: Settings },
];

export default function AdminSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const setIsSidebarExpanded = useSidebarStore((state) => state.setIsSidebarExpanded);
  
  const { user, logout } = useAuth();
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const handleLogout = () => {
    logout();
    window.location.href = "/login";
  };

  return (
    <div className="relative w-14 shrink-0 h-full z-30 select-none">
      <aside 
        onMouseEnter={() => setIsSidebarExpanded(true)}
        onMouseLeave={() => setIsSidebarExpanded(false)}
        className="group absolute top-0 left-0 flex flex-col h-full bg-white border-r border-gray-200 
                   w-14 hover:w-56 transition-all duration-150 ease-in-out shadow-md overflow-hidden"
      >
        {/* Brand Header */}
        <div className="h-[92px] py-4 flex flex-col items-center justify-between border-b border-gray-200 overflow-hidden shrink-0 w-full">
          {/* Logo Row */}
          <div className="flex items-center justify-center w-full">
            <Logo size="xs" textClassName="mt-[2px] opacity-0 group-hover:opacity-100 transition-opacity duration-150 hidden group-hover:block" />
          </div>
          
          {/* Admin Panel Row */}
          <div className="flex items-center justify-center w-full">
            <ShieldCheck className="w-[20px] h-[20px] text-blue-600 shrink-0" />
            <span className="ml-1.5 font-semibold text-sm text-gray-900 tracking-tight whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-150 hidden group-hover:block">
              Admin Panel
            </span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 py-4 flex flex-col gap-1.5 overflow-hidden px-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center h-9 w-full rounded-md transition-colors group/link overflow-hidden shrink-0",
                  isActive 
                    ? "bg-blue-50 text-blue-700" 
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                )}
                title={item.name}
              >
                <div className="w-10 flex items-center justify-center shrink-0">
                  <Icon className={cn("w-4 h-4", isActive ? "text-blue-600" : "")} />
                </div>
                <span className="text-sm font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-150">
                  {item.name}
                </span>
              </Link>
            );
          })}
        </nav>

        {/* Footer actions */}
        <div className="p-2 border-t border-gray-200">
          {/* Profile Link */}
          <Link
            href="/admin/profile"
            className={cn(
              "flex items-center w-full h-10 mb-1 rounded-md transition-colors overflow-hidden shrink-0",
              pathname === "/admin/profile"
                ? "bg-blue-50 text-blue-700"
                : "text-gray-700 hover:bg-gray-100"
            )}
            title="Admin Profile"
          >
            <div className="w-10 flex items-center justify-center shrink-0">
              {user?.profile?.avatar_url && !user?.profile?.hide_profile_picture ? (
                <img
                  src={user.profile.avatar_url}
                  alt={user.username}
                  className="w-6 h-6 rounded-full object-cover border border-gray-300"
                />
              ) : (
                <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 font-bold text-xs flex items-center justify-center border border-blue-200">
                  {user?.username ? user.username.charAt(0).toUpperCase() : "A"}
                </div>
              )}
            </div>
            <div className="flex flex-col min-w-0 opacity-0 group-hover:opacity-100 transition-opacity duration-150 leading-tight">
              <span className="text-xs font-semibold text-gray-900 truncate">
                {(user?.profile?.first_name && user?.profile?.display_full_name !== false)
                  ? `${user.profile.first_name} ${user.profile.last_name || ""}`.trim()
                  : user?.username}
              </span>
              <span className="text-[10px] text-blue-600 font-medium truncate">
                {user?.role?.name || "Staff"}
              </span>
            </div>
          </Link>

          {user?.role?.name !== "Super Admin" && (
            <Link
              href="/"
              className="flex items-center w-full h-9 mb-1 rounded-md text-gray-700 hover:bg-gray-100 transition-colors overflow-hidden shrink-0"
              title="Return to Public App"
            >
              <div className="w-10 flex items-center justify-center shrink-0">
                <Home className="w-4 h-4" />
              </div>
              <span className="text-sm font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-150">
                Return to Public App
              </span>
            </Link>
          )}

          <button
            onClick={() => setShowLogoutConfirm(true)}
            className="flex items-center w-full h-9 rounded-md text-red-600 hover:bg-red-50 transition-colors overflow-hidden shrink-0 cursor-pointer"
            title="Log Out"
          >
            <div className="w-10 flex items-center justify-center shrink-0">
              <LogOut className="w-4 h-4" />
            </div>
            <span className="text-sm font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-150">
              Log Out
            </span>
          </button>
        </div>

        {/* Logout Confirmation Modal */}
        <AnimatePresence>
          {showLogoutConfirm && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.15 }}
                className="bg-white rounded-3xl shadow-xl w-full max-w-sm overflow-hidden border border-slate-100"
              >
                <div className="p-6 text-center">
                  <div className="w-14 h-14 rounded-full bg-red-50 text-red-500 flex items-center justify-center mx-auto mb-4">
                    <LogOut className="w-7 h-7" />
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">Log Out</h3>
                  <p className="text-sm text-slate-500 mb-6 leading-relaxed">
                    Are you sure you want to log out of your account?
                  </p>
                  <div className="flex gap-3 mt-2">
                    <Button 
                      variant="secondary"
                      onClick={() => setShowLogoutConfirm(false)}
                      className="flex-1 bg-slate-100 hover:bg-slate-200 border-0"
                    >
                      Cancel
                    </Button>
                    <Button 
                      variant="danger"
                      onClick={() => {
                        setShowLogoutConfirm(false);
                        handleLogout();
                      }}
                      className="flex-1 shadow-sm shadow-red-200"
                    >
                      Yes, Log Out
                    </Button>
                  </div>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </aside>
    </div>
  );
}
