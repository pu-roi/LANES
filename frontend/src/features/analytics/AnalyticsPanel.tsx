"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";
import { Loader2, TrendingUp, MapPin, AlertCircle } from "lucide-react";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { Panel } from "@/shared/ui/Panel";
import { useOptionalMapContext } from "@/features/map/MapContext";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

interface StatItem {
  barangay?: string;
  location?: string;
  count: number;
}

interface AnalyticsStats {
  top_barangays: StatItem[];
  top_locations: StatItem[];
}

export function AnalyticsPanel() {
  const isMobile = useMediaQuery("(max-width: 768px)");
  const isDesktop = !isMobile;
  const pathname = usePathname();
  const isAdmin = pathname === "/admin/analytics";
  
  const mapContext = useOptionalMapContext();
  const isAnalyticsOpen = mapContext?.isAnalyticsOpen ?? true;
  const isAnalyticsCollapsed = mapContext?.isAnalyticsCollapsed ?? false;
  const setIsAnalyticsOpen = mapContext?.setIsAnalyticsOpen ?? (() => {});
  const setIsAnalyticsCollapsed = mapContext?.setIsAnalyticsCollapsed ?? (() => {});
  const isSavePlacePanelOpen = mapContext?.isSavePlacePanelOpen ?? false;

  const lastOpenedLeftPanel = mapContext?.lastOpenedLeftPanel;

  // When Save Place opens while Analytics is already open (and is the newer panel), dodge right and auto-collapse.
  // Uses a ref so it only fires once on the false->true transition;
  // user can still manually expand Analytics afterward.
  const isDodgingSavePlace = isSavePlacePanelOpen && lastOpenedLeftPanel === "save_place" && isDesktop && !isAdmin;
  const prevIsDodging = useRef(isDodgingSavePlace);
  const [actualDodging, setActualDodging] = useState(isDodgingSavePlace);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isDodgingSavePlace && !prevIsDodging.current) {
      // 1. Collapse first (takes 250ms)
      setIsAnalyticsCollapsed(true);
      // 2. Move exactly after collapse finishes
      timer = setTimeout(() => setActualDodging(true), 250);
    } else if (!isDodgingSavePlace && prevIsDodging.current) {
      // 1. Move first (takes 300ms)
      setActualDodging(false);
      // 2. Expand exactly after move finishes
      timer = setTimeout(() => setIsAnalyticsCollapsed(false), 300);
    }
    prevIsDodging.current = isDodgingSavePlace;
    return () => clearTimeout(timer);
  }, [isDodgingSavePlace, setIsAnalyticsCollapsed]);

  // If Analytics just opened and is forcing Save Place to dodge, wait 250ms for Save Place to collapse before sliding in.
  const isForcingSavePlaceToDodge = isSavePlacePanelOpen && lastOpenedLeftPanel === "analytics" && isDesktop && !isAdmin;
  const entranceDelay = isForcingSavePlaceToDodge ? 0.25 : 0;

  const { data, isLoading } = useQuery({
    queryKey: ["analyticsStats"],
    queryFn: () => apiClient.get<AnalyticsStats>("/analytics/stats"),
  });

  return (
    <Panel
      title="Flood Insights"
      icon={<TrendingUp className="w-5 h-5 text-red-600" />}
      iconBgClassName="bg-red-500/10"
      isCollapsed={isAdmin ? false : isAnalyticsCollapsed}
      onCollapseToggle={() => {
        if (!isAdmin) setIsAnalyticsCollapsed(!isAnalyticsCollapsed);
      }}
      isMobile={isMobile}
      isOpen={isMobile ? (isAdmin ? true : isAnalyticsOpen) : true}
      onClose={() => setIsAnalyticsOpen(false)}
      hideCollapseIcon={isAdmin}
      showDesktopClose={true}
      anchor="left"
      initialPosition={{ x: actualDodging ? 360 : 16, y: 80 }}
      panelId="analytics"
      entranceDelay={entranceDelay}
    >
      <div className="flex-1 space-y-8 no-scrollbar pb-6">
        {isLoading ? (
          <div className="flex justify-center py-10">
            <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
          </div>
        ) : (
          <>
            <section>
              <h3 className="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-orange-500" />
                Most Flooded Barangays
              </h3>
              {data?.top_barangays.length === 0 ? (
                <p className="text-sm text-slate-500 italic">No flood data available.</p>
              ) : (
                <ul className="space-y-3">
                  {data?.top_barangays.map((item, idx) => (
                    <li key={idx} className="flex items-center justify-between group">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-bold text-slate-400 w-4">{idx + 1}</span>
                        <span className="text-sm font-medium text-slate-700">{item.barangay}</span>
                      </div>
                      <span className="text-xs font-semibold bg-red-100 text-red-700 px-2 py-1 rounded-lg">
                        {item.count} alerts
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
            <section>
              <h3 className="text-sm font-semibold text-slate-800 mb-4 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-orange-500" />
                Frequent Flood Locations
              </h3>
              {data?.top_locations.length === 0 ? (
                <p className="text-sm text-slate-500 italic">No location data available.</p>
              ) : (
                <ul className="space-y-3">
                  {data?.top_locations.map((item, idx) => (
                    <li key={idx} className="flex items-center justify-between group">
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-bold text-slate-400 w-4">{idx + 1}</span>
                        <span className="text-sm font-medium text-slate-700 line-clamp-1 max-w-[200px]">
                          {item.location}
                        </span>
                      </div>
                      <span className="text-xs font-semibold bg-orange-100 text-orange-700 px-2 py-1 rounded-lg shrink-0">
                        {item.count} alerts
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}
      </div>
    </Panel>
  );
}
