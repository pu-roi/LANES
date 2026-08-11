"use client";

import { usePathname, useSearchParams, useRouter } from "next/navigation";
import { Suspense, useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, MapPin } from "lucide-react";
import { MapProvider, useMapContext } from "./MapContext";
import RoutePanel from "@/features/routing/RoutePanel";
import { ReportFab } from "@/features/hazards/ReportFab";
import { FloodReportPanel } from "@/features/hazards/FloodReportPanel";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/shared/ui";
import { AnalyticsPanel } from "@/features/analytics/AnalyticsPanel";
import { SavePlacePanel } from "@/features/places/SavePlacePanel";

const MapCanvas = dynamic(() => import("./MapCanvas"), { ssr: false });

// ── Animation Variants ─────────────────────────────────────────────────────────

/** Backdrop fades from transparent to a dark blur. */
const backdropVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.25, ease: "easeOut" as const } },
  exit: { opacity: 0, transition: { duration: 0.2, ease: "easeIn" as const } },
};

/** Action pill slides up from the FAB with a spring, fading in simultaneously. */
const actionPillVariants = {
  hidden: { opacity: 0, y: 24, scale: 0.85 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: "spring" as const, stiffness: 380, damping: 26, delay: 0.06 },
  },
  exit: {
    opacity: 0,
    y: 16,
    scale: 0.9,
    transition: { duration: 0.15, ease: "easeIn" as const },
  },
};

// ── MapLayout ──────────────────────────────────────────────────────────────────

/**
 * Inner layout component that wraps all UI over the map.
 * Because it is rendered inside MapProvider, it can fully access layout state.
 */
function MapLayout() {
  const router = useRouter();
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const isMobile = useMediaQuery("(max-width: 640px), (pointer: coarse)");
  
  const { isAuthenticated } = useAuth();
  const { error } = useToast();
  
  const { 
    activePanel, 
    setActivePanel, 
    isPickingOnMap, 
    isReportPanelOpen, 
    setIsReportPanelOpen,
    hasBottomOffset,
    isAnalyticsOpen,
    setIsAnalyticsOpen,
    setIsPickingOnMap,
    activePoint,
    setActivePoint,
    setSavedPlaces,
    isSavePlacePanelOpen,
    setIsSavePlacePanelOpen
  } = useMapContext();

  const searchParams = useSearchParams();

  useEffect(() => {
    if (pathname === "/analytics" || pathname === "/admin/analytics") {
      setIsAnalyticsOpen(true);
    }
  }, [pathname, setIsAnalyticsOpen]);

  useEffect(() => {
    if (isAuthenticated) {
      import("@/features/profile/savedPlacesApi").then(({ savedPlacesApi }) => {
        savedPlacesApi.getSavedPlaces().then(setSavedPlaces).catch(console.error);
      });
    }
  }, [isAuthenticated, setSavedPlaces]);

  // -- Event Handlers --
  // Automatically open the report panel if navigated with ?action=report
  useEffect(() => {
    if (searchParams.get("action") === "report") {
      setIsReportPanelOpen(true);
      setActivePanel("flood");
    } else if (searchParams.get("action") === "pickPostLocation") {
      setIsPickingOnMap(true);
      setActivePoint("post_location");
    }
  }, [searchParams, setIsReportPanelOpen, setActivePanel, setIsPickingOnMap, setActivePoint]);

  // The panel is expanded when it is both open and actively selected, or when Analytics is open, or when SavePlace is open.
  const isPanelExpanded = (isReportPanelOpen && activePanel === "flood") || isAnalyticsOpen || isSavePlacePanelOpen;
  
  const pillBottomClass = hasBottomOffset 
    ? "bottom-[calc(64px+env(safe-area-inset-bottom)+160px)]" 
    : "bottom-[calc(64px+env(safe-area-inset-bottom)+88px)]";

  const handleSelectFloodReport = () => {
    if (!isAuthenticated) {
      error("Login Required", "You must be logged in to report a flood.");
      return;
    }
    setIsReportPanelOpen(true);
    setActivePanel("flood");
    setIsMenuOpen(false);
  };

  const handleSelectSavePlace = () => {
    if (!isAuthenticated) {
      error("Login Required", "You must be logged in to save a place.");
      return;
    }
    setIsSavePlacePanelOpen(true);
    setActivePanel("save_place");
    setIsMenuOpen(false);
  };

  const handleCloseMenu = () => setIsMenuOpen(false);

  return (
    <>
      <MapCanvas />

      {/* -- 1. Backdrop blur overlay ---------------------------------------- */}
      <AnimatePresence>
        {isMenuOpen && (
          <motion.div
            key="fab-backdrop"
            variants={backdropVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={handleCloseMenu}
            className="fixed inset-0 z-[45] bg-slate-900/40 backdrop-blur-sm"
          />
        )}
      </AnimatePresence>

      {/* -- Desktop/Tablet Permanent Action Pills --------------------------- */}
      {!isMobile && !pathname.startsWith('/admin') && pathname !== '/analytics' && (
        <div className="fixed bottom-6 left-6 z-[40] flex flex-col gap-3">
          <button
            onClick={handleSelectSavePlace}
            className="flex items-center justify-center w-12 h-12 bg-white text-slate-800 rounded-full shadow-lg border border-gray-200 hover:bg-gray-50 active:scale-95 transition-transform"
            title="Save Place"
          >
            <MapPin className="w-5 h-5 text-blue-600" />
          </button>
        </div>
      )}

      {/* -- 2. Mobile Action Pills ------------------------------------------ */}
      <AnimatePresence>
        {isMenuOpen && (
          <div className={`fixed ${pillBottomClass} left-4 z-[46] flex flex-col gap-3`}>
            <motion.button
              key="fab-action-pill-flood"
              variants={actionPillVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              onClick={handleSelectFloodReport}
              className="flex items-center gap-3 bg-white text-slate-800 font-semibold pl-3 pr-5 py-2.5 rounded-full shadow-2xl border border-gray-200/60 hover:bg-gray-50 active:scale-95 cursor-pointer select-none"
            >
              <div className="bg-orange-100 p-2 rounded-full text-orange-600 shrink-0">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <span className="text-sm tracking-tight">Flood Report</span>
            </motion.button>

            <motion.button
              key="fab-action-pill-save"
              variants={actionPillVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              onClick={handleSelectSavePlace}
              className="flex items-center gap-3 bg-white text-slate-800 font-semibold pl-3 pr-5 py-2.5 rounded-full shadow-2xl border border-gray-200/60 hover:bg-gray-50 active:scale-95 cursor-pointer select-none"
            >
              <div className="bg-blue-100 p-2 rounded-full text-blue-600 shrink-0">
                <MapPin className="w-4 h-4" />
              </div>
              <span className="text-sm tracking-tight">Save Place</span>
            </motion.button>
          </div>
        )}
      </AnimatePresence>

      {/* -- 3. FAB Button --------------------------------------------------- */}
      {isMobile && !isPickingOnMap && !pathname.startsWith('/admin') && pathname !== '/analytics' && (
        <ReportFab
          isMenuOpen={isMenuOpen}
          isPanelExpanded={isPanelExpanded}
          onClick={() => {
            if (!isMenuOpen && !isAuthenticated) {
              error("Login Required", "You must be logged in to use map actions.");
              return;
            }
            setIsMenuOpen((prev) => !prev);
          }}
        />
      )}

      {/* -- 4. Panels ------------------------------------------------------- */}
      <AnimatePresence>
        {isAnalyticsOpen && <AnalyticsPanel />}
      </AnimatePresence>
      {!pathname.startsWith('/admin') && pathname !== "/analytics" && (
        <>
          <FloodReportPanel
            isOpen={isMobile ? isReportPanelOpen : true}
            onClose={() => setIsReportPanelOpen(false)}
          />
          <RoutePanel />
          <SavePlacePanel />
        </>
      )}

      {activePoint === "post_location" && !isMobile && (
        <div className="absolute bottom-28 left-1/2 -translate-x-1/2 z-50 bg-white/95 backdrop-blur-md rounded-2xl shadow-xl px-6 py-4 flex items-center gap-4 border border-gray-200 pointer-events-auto w-[90%] sm:w-auto">
          <MapPin className="w-5 h-5 text-red-500 animate-bounce" />
          <div className="text-sm font-semibold text-gray-800">
            Click on the map to tag your post location
          </div>
          <button 
            type="button"
            onClick={() => {
              setActivePoint(null);
              setIsPickingOnMap(false);
              router.push("/feed?openPostModal=true");
            }}
            className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-lg text-xs font-bold transition-colors"
          >
            Cancel
          </button>
        </div>
      )}

      {activePoint === "save_place_location" && !isMobile && (
        <div className="absolute bottom-28 left-1/2 -translate-x-1/2 z-50 bg-white/95 backdrop-blur-md rounded-2xl shadow-xl px-6 py-4 flex items-center gap-4 border border-gray-200 pointer-events-auto w-[90%] sm:w-auto">
          <MapPin className="w-5 h-5 text-blue-500 animate-bounce" />
          <div className="text-sm font-semibold text-gray-800">
            Click on the map to select location
          </div>
          <button 
            type="button"
            onClick={() => {
              setActivePoint(null);
              setIsPickingOnMap(false);
              setIsSavePlacePanelOpen(true);
            }}
            className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-lg text-xs font-bold transition-colors"
          >
            Cancel
          </button>
        </div>
      )}
    </>
  );
}

// -- GlobalMap ------------------------------------------------------------------

export default function GlobalMap() {
  const pathname = usePathname();

  // Completely unmount the commuter map when in the admin panel to save memory
  // EXCEPT for admin analytics which relies on the map.
  if (pathname.startsWith('/admin') && pathname !== '/admin/analytics') {
    return null;
  }

  const isMapVisible = pathname === "/map" || pathname === "/analytics" || pathname === "/admin/analytics";

  return (
    <div
      className={`fixed inset-0 z-0 transition-opacity duration-300 ${
        isMapVisible ? "opacity-100" : "opacity-0 pointer-events-none"
      }`}
    >
      <Suspense fallback={null}>
        <MapProvider>
          <MapLayout />
        </MapProvider>
      </Suspense>
    </div>
  );
}
