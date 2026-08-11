"use client";

import { type ReactNode, useRef, useEffect } from "react";
import { motion, AnimatePresence, useDragControls } from "framer-motion";
import { ChevronDown, ChevronUp, X } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/shared/ui/Card";
import { cn } from "@/lib/utils";
import { usePathname } from "next/navigation";
import { useSidebarStore } from "@/shared/stores/sidebarStore";
import { useOptionalMapContext } from "@/features/map/MapContext";

interface PanelProps {
  /** Text shown in the card header. */
  title: string;
  /** Icon element rendered inside the icon badge. */
  icon: ReactNode;
  /** Tailwind bg class for the icon badge (e.g. "bg-blue-100"). */
  iconBgClassName?: string;
  /**
   * Extra controls rendered right-of-title (before the chevron).
   * e.g. a "Clear" text button.
   */
  headerActions?: ReactNode;
  /**
   * Content shown inside the header when the panel is collapsed.
   * Only rendered on desktop; ignored on mobile.
   */
  collapsedSummary?: ReactNode;
  /** Whether the panel body is collapsed (desktop only). */
  isCollapsed: boolean;
  /** Called when the collapse toggle chevron is clicked (desktop). */
  onCollapseToggle: () => void;
  /** Whether we are rendering in a mobile viewport. */
  isMobile: boolean;
  /**
   * Controls mobile slide-up visibility.
   * Ignored on desktop (desktop card is always visible).
   */
  isOpen?: boolean;
  /** Called when the mobile close (X) button is pressed. */
  onClose?: () => void;
  /**
   * Which edge of the map the panel is anchored to.
   * Defaults to "left". When "right", the drag wrapper uses `right-0`
   * and `initialPosition.x` is treated as the distance from the right edge.
   */
  anchor?: "left" | "right";
  /**
   * Initial {x, y} position of the draggable desktop card.
   * Defaults to { x: 16, y: 80 }.
   */
  initialPosition?: { x: number; y: number };
  /** Main panel body content. Rendered inside CardContent on desktop. */
  children: ReactNode;
  /** Whether to hide the collapse chevron icon. */
  hideCollapseIcon?: boolean;
  /** Whether to show a close (X) button on desktop. */
  showDesktopClose?: boolean;
  /** Optional class name for the panel body container */
  bodyClassName?: string;
  /** Optional ID for dynamic z-indexing (stacking). */
  panelId?: string;
  /** Delay in seconds before the panel slides in (useful for sequencing). */
  entranceDelay?: number;
}

/**
 * Shared shell for map-side floating panels.
 *
 * Desktop: renders a draggable card anchored at `initialPosition`.
 * Mobile:  renders a full-screen slide-up sheet controlled by `isOpen`.
 *
 * Consumers supply the body content via `children`.
 */
export function Panel({
  title,
  icon,
  iconBgClassName = "bg-gray-100",
  headerActions,
  collapsedSummary,
  isCollapsed,
  onCollapseToggle,
  isMobile,
  isOpen = true,
  onClose,
  anchor = "left",
  initialPosition = { x: 16, y: 80 },
  children,
  hideCollapseIcon = false,
  showDesktopClose = false,
  bodyClassName,
  panelId,
  entranceDelay = 0,
}: PanelProps) {
  const dragControls = useDragControls();
  const dragStartPos = useRef({ x: 0, y: 0 });

  const pathname = usePathname();
  const isSidebarExpanded = useSidebarStore((state) => state.isSidebarExpanded);
  const isAdmin = pathname?.startsWith("/admin");
  const isRight = anchor === "right";

  const mapContext = useOptionalMapContext();
  const bringPanelToFront = mapContext?.bringPanelToFront;
  const panelZIndices = mapContext?.panelZIndices || {};

  // Bring to front on mount/open
  useEffect(() => {
    if (panelId && bringPanelToFront && isOpen) {
      bringPanelToFront(panelId);
    }
  }, [panelId, bringPanelToFront, isOpen]);

  // Calculate actual left offset for left-anchored panels
  const sidebarOffset = isAdmin ? (isSidebarExpanded ? 224 : 56) : 0;
  const targetX = isRight ? initialPosition.x : initialPosition.x + sidebarOffset;

  const handlePointerDown = (e: React.PointerEvent) => {
    dragStartPos.current = { x: e.clientX, y: e.clientY };
    dragControls.start(e.nativeEvent);
  };

  const handleHeaderClick = (e: React.MouseEvent) => {
    const dx = e.clientX - dragStartPos.current.x;
    const dy = e.clientY - dragStartPos.current.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    if (distance > 5) return;
    onCollapseToggle();
  };

  // ── Shared header markup ──────────────────────────────────────────────────
  const headerRow = (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3 min-w-0">
        <div className={cn("p-2 rounded-lg shrink-0", iconBgClassName)}>
          {icon}
        </div>
        <CardTitle className="text-[15px] font-bold tracking-tight text-gray-900 truncate">
          {title}
        </CardTitle>
      </div>
      <div className="flex items-center gap-1 shrink-0 ml-2">
        {headerActions}
        {!isMobile && (
          <>
            {showDesktopClose && onClose && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onClose();
                }}
                className="p-1 hover:bg-red-50 hover:text-red-600 rounded-md transition-colors"
                title="Close panel"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            )}
            {!hideCollapseIcon && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onCollapseToggle();
                }}
                className="p-1 hover:bg-gray-100 rounded-md transition-colors"
                title={isCollapsed ? "Expand panel" : "Collapse panel"}
              >
                {isCollapsed ? (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronUp className="w-5 h-5 text-gray-500" />
                )}
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );

  const handleMobileHeaderClick = (e: React.MouseEvent) => {
    if (!isCollapsed) return;
    const dx = e.clientX - dragStartPos.current.x;
    const dy = e.clientY - dragStartPos.current.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    if (distance > 5) return;
    onCollapseToggle();
  };

  // ── Mobile: draggable bottom sheet ────────────────────────────────────────
  if (isMobile) {
    return (
      <AnimatePresence>
        {isOpen && (
          <motion.div
            key="panel-mobile"
            drag="y"
            dragControls={dragControls}
            dragListener={false}
            dragConstraints={{ top: 0, bottom: 600 }}
            dragElastic={0.2}
            onDragEnd={(e, info) => {
              if (info.offset.y > 60 && !isCollapsed) {
                onCollapseToggle();
              } else if (info.offset.y < -60 && isCollapsed) {
                onCollapseToggle();
              }
              if (info.offset.y > 150 && onClose) {
                onClose();
              }
            }}
            initial={{ y: "100%" }}
            animate={{ y: isCollapsed ? "calc(100% - 72px)" : 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed inset-x-0 z-40 rounded-t-2xl shadow-[0_-8px_30px_rgba(0,0,0,0.12)] bg-white border-t border-gray-200"
            style={{ 
              maxHeight: "calc(100vh - 80px - 4rem - env(safe-area-inset-bottom, 0px))",
              bottom: "calc(4rem + env(safe-area-inset-bottom, 0px))"
            }}
          >
            <div 
              className="w-full flex justify-center py-3 cursor-grab active:cursor-grabbing touch-none"
              onPointerDown={handlePointerDown}
              onClick={handleMobileHeaderClick}
            >
              <div className="w-12 h-1.5 bg-gray-300 rounded-full" />
            </div>

            <div className="px-4 pb-4">
              {headerRow}
              <AnimatePresence>
                {isCollapsed && collapsedSummary && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="pt-2"
                  >
                    {collapsedSummary}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <AnimatePresence>
              {!isCollapsed && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className={cn("px-4 pb-0 overflow-y-auto max-h-[60vh]", bodyClassName)}
                >
                  {children}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    );
  }

  return (
    <motion.div
      drag
      dragControls={dragControls}
      dragListener={false}
      dragMomentum={false}
      initial={{
        x: isRight ? -targetX : targetX,
        y: initialPosition.y,
      }}
      animate={{
        x: isRight ? -targetX : targetX,
      }}
      transition={{ type: "tween", ease: "easeInOut", duration: 0.3 }}
      className={cn(
        "absolute top-0",
        !panelId && "z-40",
        isRight ? "right-0" : "left-0"
      )}
      style={panelId ? { zIndex: panelZIndices[panelId] || 40 } : undefined}
      onPointerDownCapture={() => {
        if (panelId && bringPanelToFront) {
          bringPanelToFront(panelId);
        }
      }}
    >
      <motion.div
        initial={{ x: isRight ? 100 : -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: isRight ? 100 : -100, opacity: 0 }}
        transition={{ type: "tween", ease: "easeInOut", duration: 0.3, delay: entranceDelay }}
        className="w-[340px] shadow-2xl rounded-2xl overflow-hidden border border-gray-100/50 relative bg-white/95 backdrop-blur-xl pointer-events-auto"
      >
        <Card className="border-0 shadow-none bg-transparent flex flex-col max-h-[calc(100vh-7.5rem)] overflow-hidden">
          {/* Desktop header */}
          <CardHeader 
            className="pb-3 pt-4 rounded-t-xl cursor-move touch-none select-none transition-colors hover:bg-gray-50/50"
            onPointerDown={handlePointerDown}
            onClick={handleHeaderClick}
          >
            {headerRow}

            {/* Collapsed summary slot */}
            <AnimatePresence>
              {isCollapsed && collapsedSummary && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ type: "tween", ease: "easeInOut", duration: 0.25 }}
                  className="overflow-hidden bg-white/50 backdrop-blur-sm"
                >
                  {collapsedSummary}
                </motion.div>
              )}
            </AnimatePresence>
          </CardHeader>

          {/* Collapsible body */}
          <AnimatePresence>
            {!isCollapsed && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.25, ease: "easeInOut" }}
                className="overflow-y-auto flex-1 min-h-0"
              >
                <CardContent className="space-y-4 pb-4">
                  {children}
                </CardContent>
              </motion.div>
            )}
          </AnimatePresence>
        </Card>
      </motion.div>
    </motion.div>
  );
}
