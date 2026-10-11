import type { ReactNode } from "react";

/** Independently scrolling desktop panes; mobile shows one selected pane. */
export function RecordDetailsPanels({ main, aside, showAsideOnMobile = false, mainLabel, asideLabel }: { main: ReactNode; aside?: ReactNode; showAsideOnMobile?: boolean; mainLabel: string; asideLabel: string }) {
  return <div className={`grid min-h-0 flex-1 gap-6 ${aside ? "lg:grid-cols-[minmax(0,1fr)_18rem]" : ""}`}>
    <section aria-label={mainLabel} tabIndex={0} className={`min-h-0 min-w-0 overflow-y-auto overscroll-contain pr-1 focus-visible:outline-2 focus-visible:outline-blue-500 ${showAsideOnMobile ? "hidden lg:block" : "block"}`}>{main}</section>
    {aside && <section aria-label={asideLabel} tabIndex={0} className={`min-h-0 min-w-0 overflow-y-auto overscroll-contain bg-slate-50 p-4 focus-visible:outline-2 focus-visible:outline-blue-500 ${showAsideOnMobile ? "block" : "hidden lg:block"}`}>{aside}</section>}
  </div>;
}
