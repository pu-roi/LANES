import React from "react";
import { Skeleton } from "@/shared/ui";

export default function FeedLoading() {
  return (
    <div className="w-full max-w-2xl mx-auto py-8">
      {/* Header Skeleton */}
      <div className="bg-transparent border-b border-gray-200 px-4 pt-2 pb-0 flex flex-col justify-end mb-2">
        <Skeleton className="h-7 w-48 mb-2 mx-2" />
        <div className="flex justify-between items-end px-2 pb-3">
          <div className="flex gap-6">
            <Skeleton className="h-5 w-16" />
            <Skeleton className="h-5 w-16" />
          </div>
          <Skeleton className="h-5 w-20" />
        </div>
      </div>

      {/* Create Post Input Trigger Skeleton */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4 flex items-center gap-3">
        <Skeleton className="w-10 h-10 rounded-full shrink-0" />
        <Skeleton className="flex-1 h-12 rounded-full" />
        <div className="flex items-center gap-2 border-l border-gray-100 pl-2 shrink-0">
          <Skeleton className="w-9 h-9 rounded-full" />
          <Skeleton className="w-9 h-9 rounded-full" />
        </div>
      </div>

      {/* Feed Content Skeleton */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 mt-2 overflow-hidden mb-20 p-4 space-y-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="py-6 border-b border-gray-100 last:border-b-0">
            {/* Header */}
            <div className="flex justify-between items-start mb-3">
              <div className="flex items-center gap-3">
                <Skeleton className="w-10 h-10 rounded-full" />
                <div className="space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-24" />
                </div>
              </div>
              <Skeleton className="h-6 w-24 rounded-full" />
            </div>

            {/* Content */}
            <div className="space-y-2 mb-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/6" />
            </div>

            {/* Image Placeholder (optional) */}
            {i === 1 && (
              <Skeleton className="w-full h-64 rounded-xl mb-4" />
            )}

            {/* Interaction Bar */}
            <div className="flex items-center justify-between mt-4">
              <div className="flex gap-4">
                <Skeleton className="h-8 w-24 rounded-full" />
                <Skeleton className="h-8 w-16 rounded-full" />
                <Skeleton className="h-8 w-16 rounded-full" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
