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

    // Handle in-page anchor clicks with smooth Lenis animation
    const handleAnchorClick = (e: MouseEvent) => {
      const target = (e.target as HTMLElement).closest("a");
      if (
        target &&
        target.hash &&
        target.origin === window.location.origin &&
        target.pathname === window.location.pathname
      ) {
        e.preventDefault();
        lenis.scrollTo(target.hash, { offset: -20, duration: 1.1 });
      }
    };

    document.addEventListener("click", handleAnchorClick);

    return () => {
      document.removeEventListener("click", handleAnchorClick);
      lenis.destroy();
      lenisRef.current = null;
    };
  }, []); // Empty dependency array: initialize only once!

  useEffect(() => {
    // Disable smooth wheel on map page to preserve Canvas / WebGL interaction integrity
    if (lenisRef.current) {
      if (pathname === "/map") {
        lenisRef.current.stop();
      } else {
        lenisRef.current.start();
      }
    }
  }, [pathname]);

  return <>{children}</>;
}
