"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import Lenis from "lenis";

interface SmoothScrollProps {
  children?: React.ReactNode;
}

export function SmoothScroll({ children }: SmoothScrollProps) {
  const pathname = usePathname();
  const lenisRef = useRef<Lenis | null>(null);

  useEffect(() => {
    const shouldDisable =
      pathname === "/map" ||
      pathname.startsWith("/feed") ||
      pathname.startsWith("/profile") ||
      pathname.startsWith("/register") ||
      pathname.startsWith("/login") ||
      pathname.startsWith("/auth");

    if (shouldDisable) {
      if (lenisRef.current) {
        lenisRef.current.destroy();
        lenisRef.current = null;
      }
      
      // Safety cleanup to ensure native scrolling works when Lenis is disabled
      document.documentElement.classList.remove('lenis', 'lenis-smooth', 'lenis-scrolling', 'lenis-stopped');
      document.documentElement.style.removeProperty('overflow');
      document.documentElement.style.removeProperty('height');
      document.body.style.removeProperty('overflow');
      document.body.style.removeProperty('height');
      return;
    }

    if (!lenisRef.current) {
      const lenis = new Lenis({
        duration: 1.1,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        orientation: "vertical",
        gestureOrientation: "vertical",
        smoothWheel: true,
        wheelMultiplier: 1.1,
        touchMultiplier: 1.5,
        autoRaf: true,
      });
      lenisRef.current = lenis;
    }

    const handleAnchorClick = (e: MouseEvent) => {
      if (!lenisRef.current) return;
      const target = (e.target as HTMLElement).closest("a");
      if (
        target &&
        target.hash &&
        target.origin === window.location.origin &&
        target.pathname === window.location.pathname
      ) {
        e.preventDefault();
        lenisRef.current.scrollTo(target.hash, { offset: -20, duration: 1.1 });
      }
    };

    document.addEventListener("click", handleAnchorClick);

    return () => {
      document.removeEventListener("click", handleAnchorClick);
    };
  }, [pathname]);

  useEffect(() => {
    return () => {
      if (lenisRef.current) {
        lenisRef.current.destroy();
        lenisRef.current = null;
      }
    };
  }, []);

  return <>{children}</>;
}
