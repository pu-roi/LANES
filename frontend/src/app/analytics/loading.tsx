import React from "react";
import { Skeleton } from "@/shared/ui";

export default function AnalyticsLoading() {
  return (
    <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <Skeleton className="h-10 w-64 mb-2" />
        <Skeleton className="h-5 w-96" />
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <Skeleton className="h-5 w-24" />
              <Skeleton className="h-10 w-10 rounded-lg" />
            </div>
            <Skeleton className="h-10 w-32 mb-2" />
            <Skeleton className="h-4 w-48" />
          </div>
        ))}
      </div>

      {/* Main Charts Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Chart */}
        <div className="lg:col-span-2 space-y-8">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <div className="flex justify-between items-center mb-6">
              <Skeleton className="h-6 w-48" />
              <div className="flex gap-2">
                <Skeleton className="h-8 w-24 rounded-full" />
                <Skeleton className="h-8 w-24 rounded-full" />
              </div>
            </div>
            <Skeleton className="w-full h-80 rounded-lg" />
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <Skeleton className="h-6 w-48 mb-6" />
            <Skeleton className="w-full h-64 rounded-lg" />
          </div>
        </div>

        {/* Sidebar Charts */}
        <div className="space-y-8">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <Skeleton className="h-6 w-40 mb-6" />
            <div className="flex justify-center">
              <Skeleton className="w-48 h-48 rounded-full" />
            </div>
            <div className="mt-6 space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <Skeleton className="w-3 h-3 rounded-full" />
                    <Skeleton className="h-4 w-20" />
                  </div>
                  <Skeleton className="h-4 w-12" />
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <Skeleton className="h-6 w-40 mb-6" />
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <Skeleton className="w-8 h-8 rounded-full" />
                    <Skeleton className="h-4 w-24" />
                  </div>
                  <Skeleton className="h-4 w-16" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
