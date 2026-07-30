import React from "react";
import { Skeleton } from "@/shared/ui";

export default function AdminLoading() {
  return (
    <div className="w-full h-full flex flex-col p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-10 w-48 rounded-md" />
      </div>

      {/* Tabs */}
      <div className="flex gap-2 bg-white p-2 rounded-xl border border-slate-200 shadow-sm w-fit">
        <Skeleton className="h-10 w-32 rounded-lg" />
        <Skeleton className="h-10 w-32 rounded-lg" />
        <Skeleton className="h-10 w-32 rounded-lg" />
      </div>

      {/* Table/List Area */}
      <div className="flex-1 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
        {/* Table Header */}
        <div className="p-4 border-b border-slate-200 bg-slate-50 flex gap-4">
          <Skeleton className="h-6 flex-[2]" />
          <Skeleton className="h-6 flex-1" />
          <Skeleton className="h-6 flex-1" />
          <Skeleton className="h-6 flex-1" />
          <Skeleton className="h-6 w-24" />
        </div>

        {/* Table Rows */}
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {[1, 2, 3, 4, 5, 6, 7].map((i) => (
            <div key={i} className="flex gap-4 items-center p-4 border border-slate-100 rounded-lg">
              <div className="flex-[2] flex gap-3 items-center">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="space-y-2">
                  <Skeleton className="h-5 w-48" />
                  <Skeleton className="h-4 w-32" />
                </div>
              </div>
              <Skeleton className="h-5 flex-1" />
              <Skeleton className="h-5 flex-1" />
              <Skeleton className="h-8 flex-1 rounded-full" />
              <Skeleton className="h-10 w-24 rounded-md" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
