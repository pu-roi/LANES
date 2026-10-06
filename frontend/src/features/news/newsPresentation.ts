import { parseUtcDate } from "@/lib/utils";
import type { BodyStatus, NewsFloodSummary, ProcessingStatus } from "./newsApi";
import type { FloodLocationSummaryData } from "@/shared/ui";

export function newsDate(value: string | null | undefined, missing = "Not recorded") {
  if (!value) return missing;
  const date = parseUtcDate(value);
  if (!date || Number.isNaN(date.getTime())) return missing;
  return new Intl.DateTimeFormat("en-PH", { timeZone: "Asia/Manila", month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" }).format(date);
}

export const processingLabels: Record<ProcessingStatus, string> = {
  not_recorded: "No recorded processing", pending: "Queued", processing: "Processing",
  completed: "Extraction completed", retry_wait: "Waiting for retry", failed: "Processing failed",
};

export const bodyLabels: Record<BodyStatus, string> = {
  available: "Body available", missing: "Body unavailable", error: "Retrieval error",
};

export const readable = (value: string | null | undefined) => value?.replaceAll("_", " ") || "Not recorded";

export function floodSummaryData(summary: NewsFloodSummary, publishedAt?: string | null): FloodLocationSummaryData {
  return { location: summary.location, area: summary.area, locationQualifier: summary.location_qualifier,
    waterLevel: summary.water_level, condition: summary.condition, floodTimeLabel: summary.flood_time_label,
    floodTime: newsDate(summary.flood_time, "Not stated in article"), publishedAt: newsDate(publishedAt, "Not stated"), mapStatus: summary.map_status };
}

// Only publisher HTTPS links can leave the staff interface. Article text stays plain text.
export function publisherLink(value: string) {
  try {
    const url = new URL(value);
    return url.protocol === "https:" && !url.username && !url.password ? url.href : undefined;
  } catch {
    return undefined;
  }
}
