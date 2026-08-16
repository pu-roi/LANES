"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

export interface TabItem<T extends string = string> {
  id: T;
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
  badge?: string | number;
  badgeColor?: string;
  hideLabelOnMobile?: boolean;
}

export interface TabsProps<T extends string = string> {
  tabs: TabItem<T>[];
  activeTab: T;
  onChange: (id: T) => void;
  variant?: "underline" | "pills" | "segmented";
  layoutId?: string;
  className?: string;
  tabClassName?: string;
  fullWidth?: boolean;
}

/**
 * Standardized LANES Tabs component supporting:
 * - 'segmented': Floating pill container with smooth framer-motion sliding background
 * - 'underline': Classic horizontal navigation with sliding underline bar
 * - 'pills': Distinct pill buttons with subtle background states
 */
export function Tabs<T extends string = string>({
  tabs,
  activeTab,
  onChange,
  variant = "segmented",
  layoutId = "tab-active-indicator",
  className = "",
  tabClassName = "",
  fullWidth = false,
}: TabsProps<T>) {
  if (variant === "underline") {
    return (
      <div className={cn("flex border-b border-slate-200 overflow-x-auto hide-scrollbar select-none [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden", className)}>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => onChange(tab.id)}
              className={cn(
                "relative flex items-center justify-center gap-2 py-3 px-4 text-sm font-medium transition-colors hover:text-blue-600 focus:outline-none select-none shrink-0",
                fullWidth && "flex-1 min-w-0",
                isActive ? "text-blue-600 font-semibold" : "text-slate-500 hover:text-slate-800",
                tabClassName
              )}
            >
              {Icon && (
                <Icon
                  className={cn(
                    "w-4 h-4 shrink-0 transition-colors",
                    isActive ? "text-blue-600" : "text-slate-400"
                  )}
                />
              )}
              <span className={cn(tab.hideLabelOnMobile && "hidden min-[375px]:inline")}>
                {tab.label}
              </span>
              {tab.badge !== undefined && (
                <span
                  className={cn(
                    "px-2 py-0.5 rounded-full text-[11px] font-bold",
                    tab.badgeColor || (isActive ? "bg-blue-100 text-blue-700" : "bg-slate-100 text-slate-600")
                  )}
                >
                  {tab.badge}
                </span>
              )}
              {isActive && (
                <motion.div
                  layoutId={layoutId}
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 rounded-t-full"
                  transition={{ type: "spring", stiffness: 450, damping: 35 }}
                />
              )}
            </button>
          );
        })}
      </div>
    );
  }

  if (variant === "pills") {
    return (
      <div className={cn("flex items-center gap-2 p-1 select-none overflow-x-auto hide-scrollbar [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden", className)}>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => onChange(tab.id)}
              className={cn(
                "flex items-center gap-2 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all focus:outline-none select-none shrink-0",
                fullWidth && "flex-1 justify-center",
                isActive
                  ? "bg-blue-600 text-white shadow-sm"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200 hover:text-gray-900",
                tabClassName
              )}
            >
              {Icon && <Icon className={cn("w-3.5 h-3.5", isActive ? "text-white" : "text-gray-500")} />}
              <span className={cn(tab.hideLabelOnMobile && "hidden min-[375px]:inline")}>
                {tab.label}
              </span>
              {tab.badge !== undefined && (
                <span
                  className={cn(
                    "px-1.5 py-0.5 rounded-full text-[10px] font-extrabold",
                    isActive ? "bg-blue-700 text-white" : "bg-gray-200 text-gray-700"
                  )}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    );
  }

  // Default: 'segmented' (Sleek container with sliding motion indicator)
  return (
    <div
      className={cn(
        "relative flex items-center p-1 bg-slate-100/90 border border-slate-200/80 rounded-xl select-none overflow-hidden",
        className
      )}
    >
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;

        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onChange(tab.id)}
            className={cn(
              "relative flex-1 flex items-center justify-center gap-2 py-2 px-3 text-xs font-bold transition-colors z-10 focus:outline-none select-none",
              isActive ? "text-blue-700 font-extrabold" : "text-slate-600 hover:text-slate-900",
              tabClassName
            )}
          >
            {isActive && (
              <motion.div
                layoutId={layoutId}
                className="absolute inset-0 bg-white rounded-lg shadow-sm border border-slate-200/60 z-[-1]"
                transition={{ type: "spring", stiffness: 450, damping: 35 }}
              />
            )}
            {Icon && (
              <Icon
                className={cn(
                  "w-4 h-4 transition-colors shrink-0",
                  isActive ? "text-blue-600" : "text-slate-400"
                )}
              />
            )}
            <span className={cn(tab.hideLabelOnMobile && "hidden min-[375px]:inline")}>
              {tab.label}
            </span>
            {tab.badge !== undefined && (
              <span
                className={cn(
                  "px-2 py-0.5 rounded-full text-[10px] font-extrabold transition-all",
                  tab.badgeColor || (isActive ? "bg-blue-100 text-blue-700" : "bg-slate-200 text-slate-600")
                )}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}

/**
 * Animated container wrapper for tab transitions with direction-aware sliding and hidden horizontal overflow
 */
export interface TabContentPanelProps {
  tabKey: string;
  direction?: number;
  className?: string;
  children: React.ReactNode;
}

export function TabContentPanel({
  tabKey,
  direction = 1,
  className = "",
  children,
}: TabContentPanelProps) {
  const slideVariants = {
    enter: (dir: number) => ({
      x: dir > 0 ? 20 : -20,
      opacity: 0,
    }),
    center: {
      x: 0,
      opacity: 1,
    },
    exit: (dir: number) => ({
      x: dir > 0 ? -20 : 20,
      opacity: 0,
    }),
  };

  return (
    <div className="w-full overflow-hidden">
      <AnimatePresence mode="wait" custom={direction}>
        <motion.div
          key={tabKey}
          custom={direction}
          variants={slideVariants}
          initial="enter"
          animate="center"
          exit="exit"
          transition={{ duration: 0.18, ease: "easeInOut" }}
          className={cn("w-full overflow-hidden", className)}
        >
          {children}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
