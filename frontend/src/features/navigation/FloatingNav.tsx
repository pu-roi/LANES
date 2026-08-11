"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Logo } from "@/shared/ui/Logo";
import { Home, Map as MapIcon, User, Newspaper, LogOut, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";

const NAV_ITEMS = [
  { href: "/", label: "Home", icon: Home },
  { href: "/feed", label: "Feed", icon: Newspaper },
  { href: "/map", label: "Map", icon: MapIcon },
  { href: "/profile", label: "Profile", icon: User },
] as const;

export default function FloatingNav() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const isMapPage = pathname === "/map";
  
  const u = user as any;
  const showAdminButton = u && u.role?.name !== "Commuter" && u.role?.name !== "Super Admin";

  return (
    <header className="fixed top-4 z-50 hidden sm:flex justify-center pointer-events-none pb-4 w-full select-none">
      <nav className="pointer-events-auto flex items-center gap-1 bg-white/80 backdrop-blur-md rounded-full shadow-lg border border-gray-200 px-2 py-1.5 w-max max-w-[calc(100vw-2rem)] transition-all duration-500 ease-in-out">
        <Link href="/" className="flex items-center pl-3 pr-2 hidden sm:flex transition-opacity hover:opacity-80 shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1 rounded-full" title="Go to Landing Page">
          <Logo size="xs" textClassName="mt-0.5 hidden md:block shrink-0" />
        </Link>
        <span className="w-px h-5 bg-gray-200 hidden sm:block mr-2 shrink-0" />
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "group relative flex items-center justify-center shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1",
                isMapPage ? "rounded-xl px-3 py-1.5 gap-0" : "rounded-full px-3 py-1.5 gap-0 md:gap-2",
                isActive
                  ? "text-white bg-blue-600"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              )}
              style={{ transition: 'border-radius 500ms ease-in-out, gap 500ms ease-in-out, background-color 300ms ease-in-out, color 300ms ease-in-out' }}
            >
              <Icon className={cn("shrink-0 transition-colors duration-300 ease-in-out", "h-5 w-5")} />
              
              {/* Inline text for expanded mode */}
              <span 
                className={cn(
                  "overflow-hidden whitespace-nowrap text-sm font-medium",
                  isMapPage ? "max-w-0 opacity-0" : "max-w-0 opacity-0 md:max-w-[100px] md:opacity-100"
                )}
                style={{ transition: 'max-width 500ms ease-in-out, opacity 300ms ease-in-out' }}
              >
                {label}
              </span>

              {/* Tooltip for condensed mode */}
              <span className={cn(
                "absolute top-full mt-2 whitespace-nowrap rounded-md bg-gray-900 px-2.5 py-1 text-xs font-medium text-white shadow-md transition-all duration-300 ease-out pointer-events-none",
                isMapPage 
                  ? "opacity-0 -translate-y-1 group-hover:opacity-100 group-hover:translate-y-0"
                  : "md:hidden opacity-0 -translate-y-1 group-hover:opacity-100 group-hover:translate-y-0"
              )}>
                {label}
              </span>
            </Link>
          );
        })}

        {/* Separator and Admin Button */}
        {showAdminButton && (
          <>
            <span className="w-px h-5 bg-gray-200 hidden sm:block ml-2 shrink-0" />
            <Link
              href="/admin/dashboard"
              className={cn(
                "group relative flex items-center justify-center shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1",
                isMapPage ? "rounded-xl px-3 py-1.5 gap-0" : "rounded-full px-3 py-1.5 gap-0 md:gap-2",
                "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              )}
              style={{ transition: 'border-radius 500ms ease-in-out, gap 500ms ease-in-out, background-color 300ms ease-in-out, color 300ms ease-in-out' }}
            >
              <ShieldCheck className={cn("shrink-0 transition-colors duration-300 ease-in-out", "h-5 w-5")} />
              
              {/* Inline text for expanded mode */}
              <span 
                className={cn(
                  "overflow-hidden whitespace-nowrap text-sm font-medium",
                  isMapPage ? "max-w-0 opacity-0" : "max-w-0 opacity-0 md:max-w-[100px] md:opacity-100"
                )}
                style={{ transition: 'max-width 500ms ease-in-out, opacity 300ms ease-in-out' }}
              >
                Admin
              </span>

              {/* Tooltip for condensed mode */}
              <span className={cn(
                "absolute top-full mt-2 whitespace-nowrap rounded-md bg-gray-900 px-2.5 py-1 text-xs font-medium text-white shadow-md transition-all duration-300 ease-out pointer-events-none",
                isMapPage 
                  ? "opacity-0 -translate-y-1 group-hover:opacity-100 group-hover:translate-y-0"
                  : "md:hidden opacity-0 -translate-y-1 group-hover:opacity-100 group-hover:translate-y-0"
              )}>
                Admin
              </span>
            </Link>
          </>
        )}

        {/* Separator and Log Out button (Only on Profile page) */}
        {pathname.startsWith("/profile") && (
          <>
            <span className="w-px h-5 bg-gray-200 hidden sm:block ml-2 shrink-0" />
            <button
              onClick={logout}
              className={cn(
                "group relative flex items-center justify-center shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-1 rounded-full px-3 py-1.5 gap-0 md:gap-2 text-gray-600 hover:bg-red-50 hover:text-red-600"
              )}
            >
              <LogOut className="shrink-0 transition-colors duration-300 ease-in-out h-5 w-5" />
              <span 
                className="overflow-hidden whitespace-nowrap text-sm font-medium max-w-0 opacity-0 md:max-w-[100px] md:opacity-100"
                style={{ transition: 'max-width 500ms ease-in-out, opacity 300ms ease-in-out' }}
              >
                Log Out
              </span>
              <span className="md:hidden absolute top-full mt-2 whitespace-nowrap rounded-md bg-gray-900 px-2.5 py-1 text-xs font-medium text-white shadow-md transition-all duration-300 ease-out pointer-events-none opacity-0 -translate-y-1 group-hover:opacity-100 group-hover:translate-y-0">
                Log Out
              </span>
            </button>
          </>
        )}
      </nav>
    </header>
  );
}
