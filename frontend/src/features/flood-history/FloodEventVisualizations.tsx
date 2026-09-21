"use client";

import { useMemo } from "react";
import { Area, Bar, BarChart, CartesianGrid, Cell, ComposedChart, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BarChart3, CalendarDays, Clock3, Info, MapPin, PieChart as PieChartIcon, Route, Timer, TrendingUp, type LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/shared/ui";
import type { FloodEventPlanningAnalytics } from "./floodHistoryApi";

const severityColors: Record<string, string> = { low: "#22c55e", medium: "#eab308", high: "#f97316", extreme: "#dc2626" };
const weekdayLabels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const chartHeight = 240;
const tooltipStyle = { backgroundColor: "#0f172a", border: "1px solid #1e293b", borderRadius: 8, color: "#fff", fontSize: 12 };

function formatDuration(minutes: number | null): string {
  if (minutes === null) return "No ended events";
  if (minutes < 60) return `${Math.round(minutes)} min`;
  return `${Math.floor(minutes / 60)}h ${Math.round(minutes % 60)}m`;
}

export function FloodEventVisualizations({ analytics }: { analytics: FloodEventPlanningAnalytics }) {
  const trend = useMemo(() => buildTrend(analytics), [analytics]);
  const highestBarangay = analytics.recurring_barangays[0];
  const highestRoad = analytics.frequently_affected_roads[0];
  return <>
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5"><Metric icon={BarChart3} label="Verified Flood Events" value={analytics.total_events} note={`${analytics.active_events} active; ${analytics.ended_events} ended`} /><Metric icon={Clock3} label="Ended Flood Events" value={analytics.ended_events} note="Complete official lifecycles" /><Metric icon={Timer} label="Average official duration" value={formatDuration(analytics.duration.average_minutes)} note="Ended events only" /><Metric icon={MapPin} label="Most recurring barangay" value={highestBarangay?.name ?? "—"} note={highestBarangay ? `${highestBarangay.event_count} distinct events` : "No location data"} /><Metric icon={Route} label="Most affected road" value={highestRoad?.name ?? "—"} note={highestRoad ? `${highestRoad.event_count} distinct events` : "No road data"} /></div>
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1.6fr)_minmax(20rem,0.8fr)]"><ChartCard icon={TrendingUp} title="Verified events over time" description="Distinct events and approved linked reports."><TrendChart data={trend} /></ChartCard><ChartCard icon={PieChartIcon} title="Peak verified severity" description="Highest severity reached, not exact depth."><SeverityDonut analytics={analytics} /></ChartCard></div>
    <div className="grid gap-4 xl:grid-cols-2"><ChartCard icon={Clock3} title="Official duration distribution" description="Time from verification through the final zone deactivation."><DurationChart analytics={analytics} /></ChartCard><ChartCard icon={CalendarDays} title="Verification timing pattern" description="Distinct Flood Events by Philippine verification day and hour."><VerificationHeatmap analytics={analytics} /></ChartCard></div>
    <div className="grid gap-4 xl:grid-cols-2"><ChartCard icon={MapPin} title="Recurring barangays" description="Each barangay is counted once per Flood Event."><RankingChart data={analytics.recurring_barangays} label="barangay" /></ChartCard><ChartCard icon={Route} title="Frequently affected roads" description="Each road is counted once per Flood Event."><RankingChart data={analytics.frequently_affected_roads} label="road" /></ChartCard></div>
    <ChartCard icon={Info} title="Metric definitions" description="The calculations shown on this historical planning page."><dl className="grid gap-3 text-sm sm:grid-cols-2">{Object.entries(analytics.definitions).map(([key, definition]) => <div key={key}><dt className="font-semibold capitalize text-slate-800">{key.replaceAll("_", " ")}</dt><dd className="mt-1 text-slate-600">{definition}</dd></div>)}</dl></ChartCard>
  </>;
}

function ChartCard({ icon: Icon, title, description, children }: { icon: LucideIcon; title: string; description: string; children: React.ReactNode }) {
  return <Card className="shadow-sm"><CardContent className="p-4"><h3 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-slate-900"><Icon className="h-4 w-4 text-blue-600" />{title}</h3><p className="mt-1 text-xs text-slate-500">{description}</p><div className="mt-4">{children}</div></CardContent></Card>;
}

function TrendChart({ data }: { data: Array<{ date: string; label: string; events: number; reports: number }> }) {
  return <figure aria-label="Verified Flood Events and approved linked reports over time"><ResponsiveContainer width="100%" height={chartHeight}><ComposedChart data={data} margin={{ top: 6, right: 8, left: -12, bottom: 0 }}><CartesianGrid strokeDasharray="4 4" stroke="#e2e8f0" /><XAxis dataKey="label" tick={{ fill: "#94a3b8", fontSize: 11 }} /><YAxis allowDecimals={false} tick={{ fill: "#94a3b8", fontSize: 11 }} /><Tooltip contentStyle={tooltipStyle} labelFormatter={(_, payload) => payload?.[0]?.payload.date ?? ""} /><Legend wrapperStyle={{ fontSize: 11 }} /><Area type="monotone" dataKey="events" name="Verified Flood Events" fill="#bfdbfe" stroke="#3b82f6" strokeWidth={2.5} /><Bar dataKey="reports" name="Approved linked reports" fill="#f59e0b" radius={[3, 3, 0, 0]} /></ComposedChart></ResponsiveContainer><figcaption className="sr-only">Area: verified Flood Events. Bars: approved linked reports, which do not change event totals.</figcaption></figure>;
}

function SeverityDonut({ analytics }: { analytics: FloodEventPlanningAnalytics }) {
  const data = analytics.peak_severity_distribution.map((entry) => ({ ...entry, name: entry.severity[0].toUpperCase() + entry.severity.slice(1) }));
  return <figure aria-label="Peak verified severity distribution"><ResponsiveContainer width="100%" height={chartHeight}><PieChart><Pie data={data} dataKey="event_count" nameKey="name" innerRadius={52} outerRadius={82} paddingAngle={3}>{data.map((entry) => <Cell key={entry.severity} fill={severityColors[entry.severity]} stroke="#ffffff" strokeWidth={2} />)}</Pie><Tooltip contentStyle={tooltipStyle} formatter={(value, name) => [`${value} events`, name]} /><Legend wrapperStyle={{ fontSize: 11 }} /></PieChart></ResponsiveContainer><figcaption className="sr-only">Peak verified severity counts: {data.map((entry) => `${entry.name} ${entry.event_count}`).join(", ")}.</figcaption></figure>;
}

function DurationChart({ analytics }: { analytics: FloodEventPlanningAnalytics }) {
  return <figure aria-label="Official duration distribution"><ResponsiveContainer width="100%" height={chartHeight}><BarChart data={analytics.duration.distribution} margin={{ top: 6, right: 8, left: -12, bottom: 0 }}><CartesianGrid strokeDasharray="4 4" stroke="#e2e8f0" vertical={false} /><XAxis dataKey="bucket" tick={{ fill: "#94a3b8", fontSize: 11 }} /><YAxis allowDecimals={false} tick={{ fill: "#94a3b8", fontSize: 11 }} /><Tooltip contentStyle={tooltipStyle} formatter={(value) => [`${value} events`, "Ended Flood Events"]} /><Bar dataKey="event_count" name="Ended Flood Events" fill="#3b82f6" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer><figcaption className="sr-only">Duration distribution for ended Flood Events.</figcaption></figure>;
}

function RankingChart({ data, label }: { data: Array<{ name: string; event_count: number }>; label: string }) {
  return <figure aria-label={`Most recurring ${label}s`}><ResponsiveContainer width="100%" height={chartHeight}><BarChart layout="vertical" data={data.slice(0, 8)} margin={{ top: 4, right: 16, left: 22, bottom: 0 }}><CartesianGrid strokeDasharray="4 4" stroke="#e2e8f0" horizontal={false} /><XAxis type="number" allowDecimals={false} tick={{ fill: "#94a3b8", fontSize: 11 }} /><YAxis dataKey="name" type="category" width={105} tick={{ fill: "#475569", fontSize: 11 }} /><Tooltip contentStyle={tooltipStyle} formatter={(value) => [`${value} Flood Events`, "Recurrence"]} /><Bar dataKey="event_count" name="Flood Events" fill="#3b82f6" radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer><figcaption className="sr-only">Ranked list of recurring {label}s, based on distinct Flood Events.</figcaption></figure>;
}

function VerificationHeatmap({ analytics }: { analytics: FloodEventPlanningAnalytics }) {
  const values = new Map(analytics.verification_pattern.map((entry) => [`${entry.weekday}-${entry.hour}`, entry.event_count]));
  const max = Math.max(1, ...analytics.verification_pattern.map((entry) => entry.event_count));
  return <div className="overflow-x-auto"><div className="min-w-[46rem]"><div className="grid grid-cols-[3rem_repeat(24,minmax(1.5rem,1fr))] gap-1 text-center text-[10px] text-slate-500"><span />{Array.from({ length: 24 }, (_, hour) => <span key={hour}>{hour % 3 === 0 ? `${hour}` : ""}</span>)}{weekdayLabels.flatMap((day, weekday) => [<span key={`${day}-label`} className="self-center text-right font-medium text-slate-600">{day}</span>, ...Array.from({ length: 24 }, (_, hour) => { const value = values.get(`${weekday}-${hour}`) ?? 0; return <span key={`${day}-${hour}`} title={`${day}, ${String(hour).padStart(2, "0")}:00 Philippine time: ${value} verified Flood Events`} aria-label={`${day}, ${String(hour).padStart(2, "0")}:00 Philippine time: ${value} verified Flood Events`} className={`h-6 rounded-sm border border-white ${heatClass(value, max)}`}><span className="sr-only">{value}</span></span>; })])}</div><p className="mt-3 text-xs text-slate-500">Philippine time. Darker cells mean more verified events; every cell has a readable label and count.</p></div></div>;
}

function heatClass(value: number, max: number): string {
  if (value === 0) return "bg-slate-100";
  if (value / max < 0.34) return "bg-sky-200";
  if (value / max < 0.67) return "bg-sky-500";
  return "bg-blue-800";
}

function buildTrend(analytics: FloodEventPlanningAnalytics): Array<{ date: string; label: string; events: number; reports: number }> {
  const events = new Map(analytics.events_over_time.map((entry) => [entry.date, entry.event_count]));
  const reports = new Map(analytics.approved_reports_over_time.map((entry) => [entry.date, entry.report_count]));
  return [...new Set([...events.keys(), ...reports.keys()])].sort().map((date) => ({ date, label: new Date(`${date}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" }), events: events.get(date) ?? 0, reports: reports.get(date) ?? 0 }));
}

function Metric({ icon: Icon, label, value, note }: { icon: LucideIcon; label: string; value: string | number; note: string }) {
  return <Card className="shadow-sm"><CardContent className="p-4"><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p><p className="mt-1 break-words text-xl font-extrabold text-slate-900">{value}</p><p className="mt-1 text-xs text-slate-500">{note}</p></div><div className="rounded-xl bg-blue-50 p-2.5 text-blue-600"><Icon className="h-4 w-4" /></div></div></CardContent></Card>;
}
