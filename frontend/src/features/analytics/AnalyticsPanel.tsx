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

interface AnalyticsPanelProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export function AnalyticsPanel({ isOpen: propIsOpen, onClose: propOnClose }: AnalyticsPanelProps = {}) {
  const isMobile = useMediaQuery("(max-width: 768px)");
  const isDesktop = !isMobile;
  const pathname = usePathname();
  const isAdmin = pathname.startsWith("/admin");
  
  const mapContext = useOptionalMapContext();
  const isAnalyticsOpen = propIsOpen !== undefined ? propIsOpen : (mapContext?.isAnalyticsOpen ?? true);
  const isAnalyticsCollapsed = mapContext?.isAnalyticsCollapsed ?? false;
  const setIsAnalyticsOpen = propOnClose !== undefined ? (open: boolean) => { if (!open) propOnClose(); } : (mapContext?.setIsAnalyticsOpen ?? (() => {}));
  const setIsAnalyticsCollapsed = mapContext?.setIsAnalyticsCollapsed ?? (() => {});
  const isSavePlacePanelOpen = mapContext?.isSavePlacePanelOpen ?? false;

  const lastOpenedLeftPanel = mapContext?.lastOpenedLeftPanel;

  const isDodgingSavePlace = isSavePlacePanelOpen && lastOpenedLeftPanel === "save_place" && isDesktop && !isAdmin;
  const prevIsDodging = useRef(isDodgingSavePlace);
  const [actualDodging, setActualDodging] = useState(isDodgingSavePlace);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isDodgingSavePlace && !prevIsDodging.current) {
      setIsAnalyticsCollapsed(true);
      timer = setTimeout(() => setActualDodging(true), 250);
    } else if (!isDodgingSavePlace && prevIsDodging.current) {
      setActualDodging(false);
      timer = setTimeout(() => setIsAnalyticsCollapsed(false), 300);
    }
    prevIsDodging.current = isDodgingSavePlace;
    return () => clearTimeout(timer);
  }, [isDodgingSavePlace, setIsAnalyticsCollapsed]);

  const isForcingSavePlaceToDodge = isSavePlacePanelOpen && lastOpenedLeftPanel === "analytics" && isDesktop && !isAdmin;
  const entranceDelay = isForcingSavePlaceToDodge ? 0.25 : 0;

  const isRoutingPage = pathname === "/map";
  const baseX = isRoutingPage ? 416 : 16;
  const initialX = actualDodging ? baseX + 344 : baseX;

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
      initialPosition={{ x: initialX, y: 80 }}
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
