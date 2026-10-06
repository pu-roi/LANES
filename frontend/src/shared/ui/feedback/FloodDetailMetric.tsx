import type { ReactNode } from "react";

/** Shared fact tile used by Spatial Operations and news evidence details. */
export function FloodDetailMetric({ icon, iconClassName, label, value, capitalize = false }: { icon: ReactNode; iconClassName: string; label: string; value: string; capitalize?: boolean }) {
  return <div className="flex min-w-0 items-start gap-3 rounded-xl border border-slate-200/70 bg-slate-50/80 p-3.5"><div className={`flex size-8 shrink-0 items-center justify-center rounded-lg ${iconClassName}`}>{icon}</div><div className="min-w-0"><span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">{label}</span><p className={`mt-0.5 break-words text-sm font-bold text-slate-900 ${capitalize ? "capitalize" : ""}`}>{value}</p></div></div>;
}
