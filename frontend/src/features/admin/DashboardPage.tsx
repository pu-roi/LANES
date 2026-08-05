"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getDashboardStats, getDashboardCharts } from "./adminApi";
import { Card } from "@/shared/ui/Card";
import Link from "next/link";
import { 
  Loader2, 
  AlertTriangle, 
  Map, 
  CheckSquare, 
  Users, 
  Activity, 
  ShieldCheck, 
  ArrowRight,
  Database,
  CalendarCheck,
  TrendingUp,
  PieChart,
  BarChart4,
  Clock
} from "lucide-react";

export default function DashboardPage() {
  const [hoveredPoint, setHoveredPoint] = useState<{ x: number; y: number; date: string; count: number } | null>(null);
  const [hoveredSlice, setHoveredSlice] = useState<{ severity: string; count: number; percentage: number } | null>(null);
  const [hoveredBar, setHoveredBar] = useState<number | null>(null);
  const [timelineFilter, setTimelineFilter] = useState<7 | 30>(7);

  const { data: stats, isLoading: isStatsLoading, error: statsError } = useQuery({
    queryKey: ["adminDashboardStats"],
    queryFn: () => getDashboardStats(),
    refetchInterval: 15000, // auto-refresh stats every 15s
  });

  const { data: chartsData, isLoading: isChartsLoading, error: chartsError } = useQuery({
    queryKey: ["adminDashboardCharts"],
    queryFn: () => getDashboardCharts(),
    refetchInterval: 30000, // auto-refresh charts every 30s
  });

  const isLoading = isStatsLoading || isChartsLoading;
  const error = statsError || chartsError;

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600 mb-3" />
        <p className="text-gray-500 text-sm">Loading system metrics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl max-w-2xl mx-auto shadow-sm space-y-2">
        <div className="flex items-center gap-2 font-semibold">
          <AlertTriangle className="w-5 h-5 text-rose-500" />
          <span>Failed to load dashboard metrics</span>
        </div>
        <p className="text-sm text-rose-600/90">{error.message}</p>
      </div>
    );
  }

  const metricCards = [
    {
      title: "Pending Reports",
      value: stats?.total_pending_reports ?? 0,
      description: "Needs admin review",
      icon: AlertTriangle,
      color: "amber",
      href: "/admin/reports",
      actionText: "Review queue"
    },
    {
      title: "Active Detours",
      value: stats?.total_active_zones ?? 0,
      description: "Avoidance zones active",
      icon: Map,
      color: "blue",
      href: "/admin/zones",
      actionText: "Manage zones"
    },
    {
      title: "Today's Approvals",
      value: stats?.total_approved_today ?? 0,
      description: "Routes adjusted today",
      icon: CalendarCheck,
      color: "emerald",
      href: "/admin/reports",
      actionText: "View approved"
    },
    {
      title: "Total User Accounts",
      value: stats?.total_users ?? 0,
      description: "Registered in system",
      icon: Users,
      color: "indigo",
      href: "/admin/users",
      actionText: "Manage users"
    }
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-12">
      {/* Welcome Banner */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">LANES Overview</h1>
        <p className="text-gray-500 text-sm mt-1">
          Monitor system metrics, coordinate active detours, and audit moderation workflows.
        </p>
      </div>

      {/* Stats Cards Grid */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {metricCards.map((card) => {
          const Icon = card.icon;
          return (
            <div 
              key={card.title} 
              className="bg-white rounded-2xl border border-gray-200 p-6 flex flex-col justify-between shadow-sm hover:shadow-md transition-shadow duration-200"
            >
              <div className="space-y-4">
                <div className="flex justify-between items-start">
                  <span className="text-sm font-semibold text-gray-400">{card.title}</span>
                  <div className={`p-2.5 rounded-xl bg-${card.color}-50 text-${card.color}-600`}>
                    <Icon className="w-5 h-5" />
                  </div>
                </div>
                <div>
                  <h3 className="text-3xl font-extrabold text-gray-900">{card.value}</h3>
                  <p className="text-xs text-gray-400 mt-1">{card.description}</p>
                </div>
              </div>
              <div className="border-t border-gray-100 mt-6 pt-4 flex justify-between items-center">
                <Link 
                  href={card.href} 
                  className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1.5 transition-colors group"
                >
                  {card.actionText}
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts Grid */}
      {chartsData && (
        <div className="grid gap-6 md:grid-cols-3">
          {/* Reports Timeline (Line Chart) */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm md:col-span-2 space-y-4 relative">
            <div className="flex justify-between items-center">
              <h2 className="text-sm font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-blue-600" />
                Reports Over Time
              </h2>
              <div className="flex items-center bg-gray-100 p-0.5 rounded-lg border border-gray-200">
                <button
                  onClick={() => setTimelineFilter(7)}
                  className={`text-[10px] font-bold px-2 py-1 rounded-md transition-all ${timelineFilter === 7 ? "bg-white text-blue-600 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
                >
                  7 Days
                </button>
                <button
                  onClick={() => setTimelineFilter(30)}
                  className={`text-[10px] font-bold px-2 py-1 rounded-md transition-all ${timelineFilter === 30 ? "bg-white text-blue-600 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
                >
                  30 Days
                </button>
              </div>
            </div>

            {/* SVG Line Chart */}
            <div className="relative h-48 w-full">
              {(() => {
                const rawTimeline = chartsData.reports_timeline;
                const timeline = rawTimeline.slice(-timelineFilter);
                const maxCount = Math.max(...timeline.map(d => d.count), 5);
                const width = 500;
                const height = 160;
                const paddingX = 35;
                const paddingY = 15;
                const chartWidth = width - 2 * paddingX;
                const chartHeight = height - 2 * paddingY;
                const points = timeline.map((d, i) => {
                  const x = paddingX + (i * chartWidth) / (timeline.length - 1);
                  const y = paddingY + chartHeight - (d.count / maxCount) * chartHeight;
                  return { x, y, date: d.date, count: d.count };
                });

                // Path points list
                const pathD = points.reduce((acc, p, i) => {
                  return i === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
                }, "");

                // Area path for gradient fill below line
                const areaD = points.length > 0 
                  ? `${pathD} L ${points[points.length - 1].x} ${height - paddingY} L ${points[0].x} ${height - paddingY} Z`
                  : "";

                return (
                  <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible select-none">
                    {/* Gradients */}
                    <defs>
                      <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.25" />
                        <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>

                    {/* Horizontal Grid lines */}
                    {[0, 0.25, 0.5, 0.75, 1].map((ratio, idx) => {
                      const y = paddingY + chartHeight * ratio;
                      const val = Math.round(maxCount * (1 - ratio));
                      return (
                        <g key={idx} className="opacity-40">
                          <line
                            x1={paddingX}
                            y1={y}
                            x2={width - paddingX}
                            y2={y}
                            stroke="#e2e8f0"
                            strokeWidth="1"
                            strokeDasharray="4 4"
                          />
                          <text
                            x={paddingX - 8}
                            y={y + 4}
                            textAnchor="end"
                            className="text-[9px] fill-gray-400 font-semibold"
                          >
                            {val}
                          </text>
                        </g>
                      );
                    })}

                    {/* Area fill */}
                    {areaD && <path d={areaD} fill="url(#areaGradient)" />}

                    {/* Line path */}
                    {pathD && (
                      <path
                        d={pathD}
                        fill="none"
                        stroke="#3b82f6"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="drop-shadow-sm"
                      />
                    )}

                    {/* Interactive dots */}
                    {points.map((p, i) => (
                      <circle
                        key={i}
                        cx={p.x}
                        cy={p.y}
                        r={hoveredPoint?.date === p.date ? 5.5 : 3.5}
                        fill={hoveredPoint?.date === p.date ? "#3b82f6" : "#ffffff"}
                        stroke="#3b82f6"
                        strokeWidth="2"
                        className="cursor-pointer transition-all duration-150"
                        onMouseEnter={(e) => {
                          setHoveredPoint({
                            x: p.x,
                            y: p.y,
                            date: new Date(p.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
                            count: p.count
                          });
                        }}
                        onMouseLeave={() => setHoveredPoint(null)}
                      />
                    ))}

                    {/* X-axis labels */}
                    {points.filter((_, i) => timelineFilter === 7 ? true : i % 5 === 0).map((p, idx) => (
                      <text
                        key={idx}
                        x={p.x}
                        y={height - 2}
                        textAnchor="middle"
                        className="text-[9px] fill-gray-400 font-semibold"
                      >
                        {new Date(p.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                      </text>
                    ))}
                  </svg>
                );
              })()}

              {/* Line chart tooltip overlay */}
              {hoveredPoint && (
                <div 
                  className="absolute bg-slate-900/95 backdrop-blur-sm border border-slate-800 text-white rounded-lg p-2 text-xs shadow-xl pointer-events-none z-10 transition-all duration-100 flex flex-col"
                  style={{
                    left: `${(hoveredPoint.x / 500) * 100}%`,
                    top: `${(hoveredPoint.y / 160) * 100 - 32}%`,
                    transform: "translateX(-50%)"
                  }}
                >
                  <span className="font-semibold text-[10px] text-gray-400">{hoveredPoint.date}</span>
                  <span className="font-bold text-sm text-blue-400">{hoveredPoint.count} reports</span>
                </div>
              )}
            </div>
          </div>

          {/* Severity Distribution (Pie / Donut Chart) */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm flex flex-col justify-between space-y-4">
            <h2 className="text-sm font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2">
              <PieChart className="w-4 h-4 text-blue-600" />
              Severity Breakdown
            </h2>

            {/* Donut layout */}
            {(() => {
              const distribution = chartsData.severity_distribution;
              const total = Object.values(distribution).reduce((a, b) => a + b, 0);
              const severities = [
                { key: "extreme", color: "#dc2626", label: "Extreme", hoverBg: "bg-red-500" },
                { key: "high", color: "#f97316", label: "High", hoverBg: "bg-orange-500" },
                { key: "medium", color: "#eab308", label: "Medium", hoverBg: "bg-yellow-500" },
                { key: "low", color: "#22c55e", label: "Low", hoverBg: "bg-emerald-500" }
              ];

              let accumulatedPercentage = 0;
              const slices = severities.map(s => {
                const count = distribution[s.key] || 0;
                const percentage = total > 0 ? (count / total) * 100 : 0;
                const strokeOffset = 314.16 - (314.16 * percentage) / 100;
                const strokeRotation = (accumulatedPercentage / 100) * 360;
                accumulatedPercentage += percentage;
                return { ...s, count, percentage, strokeOffset, strokeRotation };
              });

              return (
                <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-around md:flex-col md:items-center">
                  {/* SVG Circle */}
                  <div className="relative w-32 h-32">
                    <svg viewBox="0 0 120 120" className="w-full h-full -rotate-90 select-none">
                      {total === 0 ? (
                        <circle
                          cx="60"
                          cy="60"
                          r="50"
                          fill="transparent"
                          stroke="#f1f5f9"
                          strokeWidth="15"
                        />
                      ) : (
                        slices.map((slice, idx) => (
                          <circle
                            key={idx}
                            cx="60"
                            cy="60"
                            r="50"
                            fill="transparent"
                            stroke={slice.color}
                            strokeWidth="15"
                            strokeDasharray="314.16"
                            strokeDashoffset={slice.strokeOffset}
                            className="transition-all duration-300"
                            style={{
                              transformOrigin: "60px 60px",
                              transform: `rotate(${slice.strokeRotation}deg)`
                            }}
                          />
                        ))
                      )}
                    </svg>
                    {/* Centered label */}
                    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                      <span className="text-xs text-gray-400 font-bold uppercase tracking-wider">Total</span>
                      <span className="text-xl font-black text-gray-900">{total}</span>
                    </div>
                  </div>

                  {/* Legend list */}
                  <div className="flex flex-wrap md:flex-row justify-center gap-x-4 gap-y-2 text-xs font-semibold text-gray-500 w-full">
                    {slices.map((slice, idx) => (
                      <div key={idx} className="flex items-center gap-1.5 min-w-[70px]">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: slice.color }} />
                        <span>{slice.label}:</span>
                        <strong className="text-gray-900">{slice.count}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}


          </div>

          {/* Top barangays (Horizontal Bar Graph) */}
          <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-4 md:col-span-3">
            <h2 className="text-sm font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2">
              <BarChart4 className="w-4 h-4 text-blue-600" />
              Top 5 Most Flooded Barangays
            </h2>

            <div className="space-y-3.5">
              {(() => {
                const barangays = chartsData.top_barangays;
                const maxCount = barangays.length > 0 ? Math.max(...barangays.map(b => b.count)) : 1;

                return barangays.map((item, idx) => {
                  const pct = (item.count / maxCount) * 100;
                  return (
                    <div 
                      key={idx} 
                      className="space-y-1"
                      onMouseEnter={() => setHoveredBar(idx)}
                      onMouseLeave={() => setHoveredBar(null)}
                    >
                      <div className="flex justify-between text-xs font-bold text-gray-700">
                        <span className="flex items-center gap-1.5">
                          <span className="text-[10px] text-gray-400">#{idx + 1}</span>
                          {item.barangay}
                        </span>
                        <span className="text-blue-600 font-extrabold">{item.count} reports</span>
                      </div>
                      <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden relative cursor-pointer border border-slate-200/50">
                        <div 
                          className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                        {hoveredBar === idx && (
                          <div className="absolute inset-0 bg-white/10 animate-pulse pointer-events-none" />
                        )}
                      </div>
                    </div>
                  );
                });
              })()}
              {chartsData.top_barangays.length === 0 && (
                <div className="text-center py-6 text-gray-400 italic text-sm">
                  No spatial report data captured yet.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* System Status & Quick Actions */}
      <div className="grid gap-6 md:grid-cols-3">
        {/* System Health Status */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-6 md:col-span-1">
          <h2 className="text-sm font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-4 h-4 text-blue-600" />
            System Health Check
          </h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <span className="text-sm font-medium text-gray-600 flex items-center gap-2">
                <Database className="w-4 h-4 text-gray-400" />
                Spatial Database
              </span>
              <div className="flex items-center gap-1.5">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
                </span>
                <span className="text-xs font-bold text-emerald-600 capitalize">
                  {stats?.database_status || "connected"}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <span className="text-sm font-medium text-gray-600 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-gray-400" />
                Auth Token Validator
              </span>
              <span className="text-xs font-bold text-emerald-600">
                ACTIVE
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600 flex items-center gap-2">
                <Map className="w-4 h-4 text-gray-400" />
                OSRM Detour Service
              </span>
              <span className="text-xs font-bold text-emerald-600">
                OPERATIONAL
              </span>
            </div>
          </div>
        </div>

        {/* Quick Launch Panel */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm space-y-6 md:col-span-2">
          <h2 className="text-sm font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2">
            <CheckSquare className="w-4 h-4 text-blue-600" />
            Quick Administration Tasks
          </h2>

          <div className="grid gap-4 sm:grid-cols-2">
            <Link 
              href="/admin/map"
              className="p-4 border border-gray-100 hover:border-blue-100 hover:bg-blue-50/20 rounded-xl flex items-start gap-4 transition-all duration-200 group"
            >
              <div className="p-2.5 bg-blue-50 rounded-xl text-blue-600">
                <Map className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-900 group-hover:text-blue-700 transition-colors">
                  Explore Live Detour Map
                </h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Inspect the map and live routing detours inside Pasig City.
                </p>
              </div>
            </Link>

            <Link 
              href="/admin/reports"
              className="p-4 border border-gray-100 hover:border-amber-100 hover:bg-amber-50/20 rounded-xl flex items-start gap-4 transition-all duration-200 group"
            >
              <div className="p-2.5 bg-amber-50 rounded-xl text-amber-600">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-900 group-hover:text-amber-700 transition-colors">
                  Review Pending Reports
                </h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Decide on pending citizen feeds and social alerts.
                </p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
