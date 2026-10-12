"use client";

import { Button, Select } from '@/shared/ui';
import { DEFAULT_FEED_FILTERS, type FeedFilters } from '../feedApi';

const sorts = [{ value: 'newest', label: 'Newest First' }, { value: 'oldest', label: 'Oldest First' }];
const dates = [{ value: 'all', label: 'All Time' }, { value: 'today', label: 'Today (UTC)' },
  { value: '24h', label: 'Last 24 Hours' }, { value: '3d', label: 'Last 3 Days' },
  { value: '7d', label: 'Last 7 Days' }];
const statuses = [{ value: 'all', label: 'All Posts' }, { value: 'active', label: 'Active Floods' },
  { value: 'resolved', label: 'Resolved Reports' }];
const severities = [{ value: 'all', label: 'All Levels' }, { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' }, { value: 'high', label: 'High' }, { value: 'extreme', label: 'Extreme' }];
const radii = [{ value: 'auto', label: 'Auto (5–15 km)' }, { value: '1000', label: '1 km' },
  { value: '3000', label: '3 km' }, { value: '5000', label: '5 km' }, { value: '10000', label: '10 km' }];

export const FILTER_QUERY_KEYS = { sort: 'sort', dateRange: 'date_range', floodStatus: 'flood_status',
  severity: 'severity', radius: 'radius' } as const;

export function readFeedFilters(params: Pick<URLSearchParams, 'get'>): FeedFilters {
  const values = { sorts, dates, statuses, severities, radii };
  const options = { sort: values.sorts, dateRange: values.dates, floodStatus: values.statuses,
    severity: values.severities, radius: values.radii };
  const filters = { ...DEFAULT_FEED_FILTERS };
  for (const key of Object.keys(FILTER_QUERY_KEYS) as (keyof FeedFilters)[]) {
    const value = params.get(FILTER_QUERY_KEYS[key]);
    if (options[key].some(option => option.value === value)) Object.assign(filters, { [key]: value });
  }
  return filters;
}

export function CommunityFeedFilters({ filters, nearby, onChange }: {
  filters: FeedFilters; nearby: boolean; onChange: (filters: FeedFilters) => void;
}) {
  const change = (key: keyof FeedFilters, value: string | number) => onChange({ ...filters, [key]: value });
  return (
    <section id="community-feed-filters" aria-label="Community feed filters" className="bg-white rounded-xl border border-gray-200/80 shadow-xs px-3.5 py-3 sm:px-4 mb-2.5">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 [&>*]:min-w-0">
        <Select label="Sort posts" options={sorts} value={filters.sort} onChange={e => change('sort', e.target.value)} />
        <Select label="Date posted" options={dates} value={filters.dateRange} onChange={e => change('dateRange', e.target.value)} />
        <Select label="Flood status" options={statuses} value={filters.floodStatus} onChange={e => change('floodStatus', e.target.value)} />
        <Select label="Flood severity" options={severities} value={filters.severity} onChange={e => change('severity', e.target.value)} />
        {nearby && <Select label="Nearby radius" options={radii} value={filters.radius} onChange={e => change('radius', e.target.value)} />}
      </div>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-gray-500 flex-1 min-w-0">Status and severity apply to public, approved flood reports. Resolved reports belong to ended flood events and are no longer active.</p>
        <Button variant="ghost" size="sm" onClick={() => onChange({ ...DEFAULT_FEED_FILTERS })}>Reset Filters</Button>
      </div>
    </section>
  );
}
