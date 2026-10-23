import type { ReactNode } from "react";

/** Fixed panes scroll independently; flow content uses its dialog's scroll area. */
export function RecordDetailsPanels({ main, aside, scrollable = true, showAsideOnMobile = false, mainLabel, asideLabel }: { main: ReactNode; aside?: ReactNode; scrollable?: boolean; showAsideOnMobile?: boolean; mainLabel: string; asideLabel: string }) {
  const scrollClasses = scrollable ? "overflow-y-auto overscroll-contain" : "";
  return <div className={`grid min-h-0 flex-1 gap-6 ${aside ? "lg:grid-cols-[minmax(0,1fr)_18rem]" : ""}`}>
    <section aria-label={mainLabel} tabIndex={0} className={`min-h-0 min-w-0 ${scrollClasses} pr-1 focus-visible:outline-2 focus-visible:outline-blue-500 ${showAsideOnMobile ? "hidden lg:block" : "block"}`}>{main}</section>
    {aside && <section aria-label={asideLabel} tabIndex={0} className={`min-h-0 min-w-0 ${scrollClasses} bg-slate-50 p-4 focus-visible:outline-2 focus-visible:outline-blue-500 ${showAsideOnMobile ? "block" : "hidden lg:block"}`}>{aside}</section>}
  </div>;
}
