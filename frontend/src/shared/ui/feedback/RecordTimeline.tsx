import type { ReactNode } from "react";

export interface RecordTimelineEntry {
  id: string | number;
  label: string;
  timestamp: string;
  description?: ReactNode;
  content?: ReactNode;
}

/** Shared chronological styling based on Flood History's incident timeline. */
export function RecordTimeline({ entries, emptyMessage }: { entries: RecordTimelineEntry[]; emptyMessage: string }) {
  return <ol className="mt-3 space-y-5 border-l border-slate-200 pl-4">
    {entries.length ? entries.map((entry) => <li key={entry.id} className="relative min-w-0"><span aria-hidden="true" className="absolute -left-[1.3rem] top-1 size-2 rounded-full bg-blue-500 ring-4 ring-white" /><p className="break-words text-xs font-semibold uppercase tracking-wide text-blue-700">{entry.label}</p>{entry.description && <div className="mt-1 break-words text-sm text-slate-800">{entry.description}</div>}<p className="mt-1 text-xs text-slate-500">{entry.timestamp}</p>{entry.content && <div className="mt-3">{entry.content}</div>}</li>) : <li className="text-sm text-slate-500">{emptyMessage}</li>}
  </ol>;
}
