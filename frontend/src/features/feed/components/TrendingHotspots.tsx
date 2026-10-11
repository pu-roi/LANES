'use client';

import Link from 'next/link';
import { Flame, RefreshCw, TrendingUp } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/shared/ui';
import { getTrendingHotspots } from '../feedApi';

export function TrendingHotspots({ onNavigate }: { onNavigate?: () => void }) {
  const { data, isPending, isError, refetch, isFetching } = useQuery({
    queryKey: ['feed', 'hotspots'],
    queryFn: getTrendingHotspots,
    staleTime: 30_000,
    refetchInterval: 60_000,
    retry: 1,
  });

  return (
    <section aria-label="Trending Hotspots" className="space-y-1">
      <h3 className="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1">
        <TrendingUp className="w-3.5 h-3.5" aria-hidden="true" />
        Trending Hotspots
      </h3>
      {isError ? (
        <div className="px-3 py-2 space-y-2">
          <p role="alert" className="text-sm text-red-600">Couldn’t load recent hotspots.</p>
          <Button variant="ghost" size="sm" className="w-full gap-2 bg-blue-50 text-blue-600 hover:bg-blue-100 hover:text-blue-700 font-medium" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'motion-safe:animate-spin' : ''}`} aria-hidden="true" />
            {isFetching ? 'Retrying…' : 'Retry'}
          </Button>
        </div>
      ) : isPending ? (
        <div role="status" className="px-3 py-2">
          <span className="sr-only">Loading recent hotspots…</span>
          <div aria-hidden="true" className="motion-safe:animate-pulse flex flex-col gap-2">
            <div className="h-4 bg-gray-200 rounded w-3/4" />
            <div className="h-4 bg-gray-200 rounded w-1/2" />
          </div>
        </div>
      ) : data.hotspots.length === 0 ? (
        <div className="px-3 py-2 text-sm text-gray-500 select-none">
          <p>No trending places in the last {data.window_hours} hours.</p>
        </div>
      ) : (
        <>
          {data.hotspots.map((hotspot) => (
            <Link
              key={hotspot.id}
              href={`/map?lat=${hotspot.latitude}&lng=${hotspot.longitude}&zoom=15`}
              onClick={onNavigate}
              title={`${hotspot.post_count} posts from ${hotspot.contributor_count} people in the last ${data.window_hours} hours`}
              className="min-h-11 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-xl transition-colors flex justify-between items-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            >
              <span className="flex items-center gap-3 min-w-0">
                <span className="w-6 h-6 flex items-center justify-center bg-orange-100 rounded-full shrink-0">
                  <Flame className="w-3.5 h-3.5 text-orange-500" aria-hidden="true" />
                </span>
                <span className="truncate">{hotspot.name}</span>
              </span>
              <span className="text-xs text-gray-500 shrink-0">{hotspot.post_count} posts</span>
            </Link>
          ))}
          <p className="px-3 pt-1 text-xs text-gray-500">Community activity · {data.window_hours === 24 ? 'Last' : 'Past'} {data.window_hours} hours</p>
        </>
      )}
    </section>
  );
}
