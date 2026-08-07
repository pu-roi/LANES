"use client";

import { usePathname, useRouter } from "next/navigation";
import FloatingNav from "./FloatingNav";
import MobileNav from "./MobileNav";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { useEffect, useState } from "react";

export default function NavigationWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isLoading, isAuthenticated } = useAuth();

  const [isRedirecting, setIsRedirecting] = useState(false);

  // Route Guards
  useEffect(() => {
    if (isLoading) return;

    const isAdminRoute = pathname.startsWith("/admin");
    const isPrivateRoute = ["/profile", "/report", "/feed/create"].some((route) => pathname.startsWith(route));

    if ((isAdminRoute || isPrivateRoute) && !isAuthenticated) {
      setIsRedirecting(true);
      router.replace("/login");
    } else if (isAdminRoute && user && user.role?.name === "Commuter") {
      setIsRedirecting(true);
      router.replace("/");
    } else {
      setIsRedirecting(false);
    }
  }, [pathname, isAuthenticated, isLoading, user, router]);

  if (isRedirecting || (isLoading && (pathname.startsWith("/admin") || ["/profile", "/report", "/feed/create"].some((route) => pathname.startsWith(route))))) {
    return null;
  }

  // Hide the global navigation bars on the Admin pages
  if (pathname.startsWith("/admin")) {
    return <>{children}</>;
  }

  const isMapPage = pathname === "/map";
  const isLandingPage = pathname === "/";
  const isFeedPage = pathname.startsWith("/feed");

  return (
    <div 
      className={cn(
        "flex-1 flex flex-col w-full sm:pb-0",
        isLandingPage ? "bg-blue-50" : (!isMapPage ? "bg-gray-50" : ""),
        !isMapPage && "pb-[calc(var(--bottom-nav-height)+env(safe-area-inset-bottom))]"
      )}
    >
      <FloatingNav />
      {/* Background Mask for FloatingNav to hide scrolling content - ONLY on Feed Page */}
      {isFeedPage && (
        <div className="fixed top-0 left-0 right-0 h-[70px] bg-gray-50/75 backdrop-blur-lg border-b border-gray-200 z-40 hidden sm:block"></div>
      )}
      <main className={cn(
        "flex-1 flex flex-col w-full min-w-0 relative z-0",
        (!isMapPage && !pathname.startsWith('/profile')) && "sm:pt-[70px]" // Safe zone padding
      )}>
        {children}
      </main>
      <MobileNav />
    </div>
  );
}
