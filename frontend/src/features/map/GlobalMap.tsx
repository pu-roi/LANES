"use client";

import { usePathname, useSearchParams, useRouter } from "next/navigation";
import { Suspense, useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Layers3, MapPin, Newspaper } from "lucide-react";
import { MapProvider, useMapContext } from "./MapContext";
import RoutePanel from "@/features/routing/RoutePanel";
import { ReportFab } from "@/features/hazards/ReportFab";
import { FloodReportPanel } from "@/features/hazards/FloodReportPanel";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { useAuth } from "@/hooks/useAuth";
import { AnalyticsPanel } from "@/features/analytics/AnalyticsPanel";
import { SavePlacePanel } from "@/features/places/SavePlacePanel";
import { Panel } from "@/shared/ui/layout";
import { NewsAlertsPanel } from "@/features/news/NewsAlertsPanel";
import { useQueryClient } from "@tanstack/react-query";


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
  const queryClient = useQueryClient();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isNewsOpen, setIsNewsOpen] = useState(false);
  const openNews = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: ["publicNewsAlerts"], refetchType: "none" });
    setIsMenuOpen(false);
    setIsNewsOpen(true);
  }, [queryClient]);
  const closeNews = useCallback(() => setIsNewsOpen(false), []);
  const isMobile = useMediaQuery("(max-width: 640px), (pointer: coarse)");
  
  const { isAuthenticated } = useAuth();
  
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
    setIsSavePlacePanelOpen,
    is3DMode,
    hazardScenario,
    setHazardScenario,
    isHazardPanelOpen,
    setIsHazardPanelOpen,
  } = useMapContext();

  const searchParams = useSearchParams();
  const hasCompetingNewsPanel = isAnalyticsOpen || isSavePlacePanelOpen || isHazardPanelOpen || (isMobile && isReportPanelOpen && activePanel === "flood");

  const showNews = isNewsOpen && !hasCompetingNewsPanel;

  useEffect(() => {
    if (pathname === "/analytics" || pathname === "/admin/analytics") {
      setIsAnalyticsOpen(true);
    }
  }, [pathname, setIsAnalyticsOpen]);

  useEffect(() => {
    if (isAuthenticated) {
      import("@/features/places/savedPlacesApi").then(({ savedPlacesApi }) => {
        savedPlacesApi.getSavedPlaces().then(setSavedPlaces).catch(console.error);
      });
    } else {
      setSavedPlaces([]);
    }
  }, [isAuthenticated, setSavedPlaces]);

  // -- Event Handlers --
  // Automatically open the report panel if navigated with ?action=report, or saveplace with ?panel=saveplace
  useEffect(() => {
    const action = searchParams.get("action");
    const panel = searchParams.get("panel");

    if (action === "report") {
      setIsReportPanelOpen(true);
      setActivePanel("flood");
    } else if (action === "pickPostLocation") {
      setIsPickingOnMap(true);
      setActivePoint("post_location");
    } else if (panel === "saveplace") {
      setIsSavePlacePanelOpen(true);
      setActivePanel("save_place");
    } else if (panel === "analytics") {
      setIsAnalyticsOpen(true);
    }
  }, [searchParams, setIsReportPanelOpen, setIsSavePlacePanelOpen, setIsAnalyticsOpen, setActivePanel, setIsPickingOnMap, setActivePoint]);

  // Keep the FAB beneath whichever mobile panel is currently expanded.
  const isPanelExpanded = (isReportPanelOpen && activePanel === "flood") || isAnalyticsOpen || isSavePlacePanelOpen || isHazardPanelOpen || (isMobile && activePanel === "route");
  
  const pillBottomClass = hasBottomOffset 
    ? "bottom-[calc(64px+env(safe-area-inset-bottom)+160px)]" 
    : "bottom-[calc(64px+env(safe-area-inset-bottom)+88px)]";

  const handleSelectFloodReport = () => {
    setIsReportPanelOpen(true);
    setActivePanel("flood");
    setIsMenuOpen(false);
  };

  const handleCloseFloodReport = () => {
    setIsReportPanelOpen(false);
    setActivePanel(null);
    if (searchParams.get("action") === "report") {
      router.replace("/map", { scroll: false });
    }
  };

  const handleSelectSavePlace = () => {
    setIsSavePlacePanelOpen(true);
    setActivePanel("save_place");
    setIsMenuOpen(false);
  };

  const handleSelectHazard = () => {
    setIsReportPanelOpen(false);
    setIsSavePlacePanelOpen(false);
    setActivePanel(null);
    setIsHazardPanelOpen(true);
    setIsMenuOpen(false);
  };

  const handleCloseMenu = () => setIsMenuOpen(false);

  return (
    <>
      <MapCanvas />
      {pathname === "/map" && !isPickingOnMap && !hasCompetingNewsPanel && <NewsAlertsPanel isMobile={isMobile} open={showNews} onOpen={openNews} onClose={closeNews} />}

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


      {/* -- 2. Mobile Action Pills ------------------------------------------ */}
      <AnimatePresence>
        {isMenuOpen && (
          <div className={`fixed ${pillBottomClass} left-4 z-[46] flex flex-col gap-3`}>
            {pathname === "/map" && <motion.button type="button" variants={actionPillVariants} initial="hidden" animate="visible" exit="exit" onClick={openNews} className="flex items-center gap-3 rounded-full border border-gray-200/60 bg-white py-2.5 pl-3 pr-5 text-left font-semibold text-slate-800 shadow-2xl hover:bg-gray-50"><span className="shrink-0 rounded-full bg-slate-100 p-2 text-slate-600"><Newspaper className="h-4 w-4" aria-hidden="true" /></span><span className="text-sm tracking-tight">News alerts</span></motion.button>}
            {pathname === "/map" && is3DMode && (
              <motion.button
                key="fab-action-pill-hazard"
                variants={actionPillVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                onClick={handleSelectHazard}
                className="flex items-center gap-3 rounded-full border border-gray-200/60 bg-white py-2.5 pl-3 pr-5 text-left font-semibold text-slate-800 shadow-2xl hover:bg-gray-50"
              >
                <span className="shrink-0 rounded-full bg-orange-100 p-2 text-orange-600"><Layers3 className="h-4 w-4" /></span>
                <span className="text-sm tracking-tight">Flood Hazard</span>
              </motion.button>
            )}
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
          onClick={() => setIsMenuOpen((prev) => !prev)}
        />
      )}

      {/* -- 4. Panels ------------------------------------------------------- */}
      <AnimatePresence>
        {isAnalyticsOpen && <AnalyticsPanel />}
      </AnimatePresence>
      <AnimatePresence>
        <SavePlacePanel />
      </AnimatePresence>
      {isMobile && pathname === "/map" && is3DMode && (
        <Panel
          title="UP NOAH Flood Hazard"
          icon={<Layers3 className="h-4 w-4 text-orange-600" />}
          iconBgClassName="bg-orange-100"
          isMobile
          isOpen={isHazardPanelOpen}
          onClose={() => setIsHazardPanelOpen(false)}
          isCollapsed={false}
          onCollapseToggle={() => {}}
          mobileHeight="185px"
          bodyClassName="flex flex-col gap-2"
        >
          <div className="flex gap-2" role="group" aria-label="Flood hazard rainfall scenarios">
            <button
              type="button"
              aria-pressed={hazardScenario === null}
              onClick={() => setHazardScenario(null)}
              className={`min-w-0 flex-1 rounded-lg px-1 py-2 text-xs font-bold transition-colors ${hazardScenario === null ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"}`}
            >
              Off
            </button>
            {([100, 25, 5] as const).map((scenario) => (
              <button
                key={scenario}
                type="button"
                aria-pressed={hazardScenario === scenario}
                onClick={() => setHazardScenario(scenario)}
                className={`min-w-0 flex-1 rounded-lg px-1 py-2 text-xs font-bold transition-colors ${hazardScenario === scenario ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"}`}
              >
                {scenario}-Year
              </button>
            ))}
          </div>
          <p className="text-[11px] text-slate-600">Modeled flood hazard, not current flooding.</p>
        </Panel>
      )}
      {!pathname.startsWith('/admin') && pathname !== "/analytics" && (
        <>
          <div className={showNews ? "hidden" : "contents"}><FloodReportPanel
            isOpen={isMobile ? (isReportPanelOpen && activePanel === "flood") : true}
            onClose={handleCloseFloodReport}
          /></div>
          <RoutePanel />
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
