"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Map as MapIcon, User, Newspaper, LogIn } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";

const MOBILE_NAV_ITEMS = [
  { href: "/", label: "Home", icon: Home },
  { href: "/feed", label: "Feed", icon: Newspaper },
  { href: "/map", label: "Map", icon: MapIcon },
  { href: "/profile", label: "Profile", icon: User },
] as const;

export default function MobileNav() {
  const pathname = usePathname();
  const { user } = useAuth();

  const redirectTarget = (!pathname.startsWith("/login") && !pathname.startsWith("/register") && !pathname.startsWith("/verify"))
    ? pathname
    : "/feed";

  return (
    <nav className="fixed bottom-0 w-full bg-white border-t border-gray-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] sm:hidden z-50 pb-safe select-none">
      <div className="relative flex justify-around items-center h-16 px-2">
        {MOBILE_NAV_ITEMS.map((item) => {
          const isProfileItem = item.href === "/profile";
          const actualHref = isProfileItem && !user ? `/login?redirect=${encodeURIComponent(redirectTarget)}` : item.href;
          const actualLabel = isProfileItem && !user ? "Sign In" : item.label;
          const Icon = isProfileItem && !user ? LogIn : item.icon;

          const isActive = isProfileItem && !user
            ? pathname.startsWith("/login")
            : (pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href)));
          
          return (
            <Link
              key={item.href}
              href={actualHref}
              className={cn(
                "relative flex flex-col items-center justify-center w-full h-full space-y-1 transition-colors duration-300 tap-highlight-transparent z-10",
                isActive ? "text-white" : "text-gray-500 hover:text-gray-900"
              )}
            >
              <div className={cn(
                "absolute inset-y-1.5 inset-x-3 bg-blue-600 rounded-xl -z-10 transition-opacity duration-300",
                isActive ? "opacity-100" : "opacity-0"
              )} />
              <Icon className={cn("h-5 w-5 transition-transform", isActive ? "scale-110 mt-0.5" : "scale-100")} />
              <span className={cn("text-[10px] font-medium transition-colors duration-300", isActive ? "text-blue-100" : "text-gray-500")}>
                {actualLabel}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
