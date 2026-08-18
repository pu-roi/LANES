"use client";

import React from 'react';
import { CloudRain, Newspaper, Trophy, Medal } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { getTopReporters, TopReporter } from './feedApi';

/** Rank badge colours for positions 1–3. */
const RANK_STYLES: Record<number, string> = {
  1: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  2: 'bg-gray-100 text-gray-600 border-gray-300',
  3: 'bg-orange-100 text-orange-600 border-orange-300',
};

function ReporterRow({ reporter }: { reporter: TopReporter }) {
  const initials = reporter.username.slice(0, 2).toUpperCase();
  const rankStyle = RANK_STYLES[reporter.rank] ?? 'bg-blue-50 text-blue-500 border-blue-200';

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <span
          className={`w-6 h-6 flex items-center justify-center rounded-full border text-[10px] font-bold flex-shrink-0 ${rankStyle}`}
        >
          {reporter.rank}
        </span>

        {reporter.avatar_url ? (
          <img
            src={reporter.avatar_url}
            alt={reporter.username}
            className="w-8 h-8 rounded-full object-cover flex-shrink-0"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center flex-shrink-0">
            <span className="text-[10px] font-bold text-white">{initials}</span>
          </div>
        )}

        <span className="text-sm font-medium text-gray-800 truncate max-w-[110px]">
          {reporter.username}
        </span>
      </div>

      <span className="text-xs font-semibold text-blue-600 whitespace-nowrap">
        {reporter.report_count} {reporter.report_count === 1 ? 'report' : 'reports'}
      </span>
    </div>
  );
}

function LeaderboardSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded-full bg-gray-200" />
            <div className="w-8 h-8 rounded-full bg-gray-200" />
            <div className="h-3.5 w-24 bg-gray-200 rounded" />
          </div>
          <div className="h-3 w-14 bg-gray-200 rounded" />
        </div>
      ))}
    </div>
  );
}

import { useWeather } from '@/hooks/useWeather';

export function RightSidebar() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['top-reporters'],
    queryFn: () => getTopReporters(5),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const { data: weather, isLoading: weatherLoading } = useWeather();

  return (
    <aside className="w-80 flex-shrink-0 flex flex-col h-[calc(100vh-86px)] sticky top-[86px] overflow-y-auto hidden lg:flex px-6 py-6 space-y-6">
      
      {/* Weather Widget */}
      <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <CloudRain className="w-5 h-5 text-blue-500" />
          <h3 className="font-semibold text-gray-900">Current Weather</h3>
        </div>
        <div className="space-y-3">
          {weatherLoading ? (
            <div className="h-16 bg-gray-100 animate-pulse rounded-xl" />
          ) : weather && weather.temp !== "--" ? (
            <div className="p-3 bg-blue-50/50 rounded-xl border border-blue-100 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-900 capitalize">{weather.condition}</p>
                <p className="text-xs text-blue-700 mt-1">
                  {weather.location} • {weather.temp}°C
                </p>
                {(weather.precip_mm !== undefined) && (
                  <p className="text-[10px] font-semibold text-blue-800 mt-1.5 bg-blue-200/50 inline-block px-1.5 py-0.5 rounded border border-blue-300/50">
                    🌧️ {weather.precip_mm} mm/h
                  </p>
                )}
              </div>
              <img 
                src={`https://cdn.jsdelivr.net/npm/@meteocons/svg@0.1.0/fill/${weather.icon}.svg`}
                alt={weather.condition}
                className="w-16 h-16 drop-shadow-sm"
              />
            </div>
          ) : (
            <p className="text-xs text-gray-500">Weather unavailable</p>
          )}
        </div>
      </div>

      {/* News Widget */}
      <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <Newspaper className="w-5 h-5 text-purple-500" />
          <h3 className="font-semibold text-gray-900">Local Updates</h3>
        </div>
        <div className="space-y-3">
          <div className="group cursor-pointer">
            <p className="text-sm font-medium text-gray-900 group-hover:text-blue-600 transition-colors line-clamp-2">
              City Council announces new drainage clearing schedule for the rainy season.
            </p>
            <p className="text-xs text-gray-500 mt-1">2 hours ago</p>
          </div>
          <hr className="border-gray-100" />
          <div className="group cursor-pointer">
            <p className="text-sm font-medium text-gray-900 group-hover:text-blue-600 transition-colors line-clamp-2">
              Main bridge repairs completed early, reducing bypass traffic.
            </p>
            <p className="text-xs text-gray-500 mt-1">5 hours ago</p>
          </div>
        </div>
      </div>

      {/* Top Reporters Leaderboard */}
      <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <Trophy className="w-5 h-5 text-yellow-500" />
          <h3 className="font-semibold text-gray-900">Top Reporters</h3>
        </div>

        {isLoading && <LeaderboardSkeleton />}

        {isError && (
          <p className="text-xs text-gray-400 text-center py-4">
            Could not load leaderboard.
          </p>
        )}

        {!isLoading && !isError && data && data.reporters.length === 0 && (
          <div className="flex flex-col items-center gap-2 py-6 text-center">
            <Medal className="w-8 h-8 text-gray-300" />
            <p className="text-xs text-gray-400">
              No reporters yet. Be the first!
            </p>
          </div>
        )}

        {!isLoading && !isError && data && data.reporters.length > 0 && (
          <div className="space-y-3">
            {data.reporters.map((reporter) => (
              <ReporterRow key={reporter.user_id} reporter={reporter} />
            ))}
          </div>
        )}
      </div>
      
    </aside>
  );
}
