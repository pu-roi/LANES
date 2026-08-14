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
    const isPublicRoute = !isAdminRoute && !pathname.startsWith("/login") && !pathname.startsWith("/register") && !pathname.startsWith("/verify");

    if (!isAuthenticated) {
      if (isAdminRoute || isPrivateRoute) {
        setIsRedirecting(true);
        const searchParams = new URLSearchParams();
        searchParams.set("redirect", pathname);
        router.replace(`/login?${searchParams.toString()}`);
      } else {
        setIsRedirecting(false);
      }
    } else {
      // Authenticated user checks
      const u = user as any;
      if (isAdminRoute && u?.role?.name === "Commuter") {
        setIsRedirecting(true);
        router.replace("/");
      } else if (isPublicRoute && u?.role?.name === "Super Admin") {
        setIsRedirecting(true);
        router.replace("/admin/dashboard");
      } else {
        setIsRedirecting(false);
      }
    }
  }, [pathname, isAuthenticated, isLoading, user, router]);

  const isProtected = pathname.startsWith("/admin") || ["/profile", "/report", "/feed/create"].some((route) => pathname.startsWith(route));
  const showLoader = isRedirecting || (isLoading && isProtected);

  const loaderOverlay = showLoader ? (
    <div className="fixed inset-0 z-[9999] bg-gray-50 flex items-center justify-center">
      <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
    </div>
  ) : null;

  // Hide the global navigation bars on the Admin pages
  if (pathname.startsWith("/admin")) {
    return (
      <>
        {loaderOverlay}
        {children}
      </>
    );
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
      {loaderOverlay}
      <FloatingNav />
      {/* Background Mask for FloatingNav to hide scrolling content - ONLY on Feed Page */}
      {isFeedPage && (
        <div className="fixed top-0 left-0 right-0 h-[70px] bg-gray-50/75 backdrop-blur-lg border-b border-gray-200 z-40 hidden sm:block"></div>
      )}
      <main className={cn(
        "flex-1 flex flex-col w-full min-w-0 relative z-0",
        (!isMapPage && !pathname.startsWith('/profile') && !pathname.startsWith('/login') && !pathname.startsWith('/register')) && "sm:pt-[70px]" // Safe zone padding
      )}>
        {children}
      </main>
      <MobileNav />
    </div>
  );
}
