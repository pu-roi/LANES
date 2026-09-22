import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Safely parses a date string, timestamp, or Date object as UTC.
 * If given an ISO-like date string without an explicit timezone suffix
 * (no 'Z' and no '+/-HH:mm'), appends 'Z' to prevent browsers from
 * erroneously parsing UTC timestamps as local time (ECMA-262).
 */
export function parseUtcDate(input: string | Date | number | null | undefined): Date | null {
  if (input === null || input === undefined || input === "") return null;
  if (input instanceof Date) return isNaN(input.getTime()) ? null : input;
  if (typeof input === "number") {
    const d = new Date(input);
    return isNaN(d.getTime()) ? null : d;
  }
  const str = input.trim();
  if (!str) return null;
  // If string already has Z or explicit offset (+HH:MM or -HH:MM), parse directly
  const hasTimezone = str.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(str) || /[+-]\d{4}$/.test(str);
  const normalizedStr = hasTimezone ? str : `${str}Z`;
  const parsed = new Date(normalizedStr);
  return isNaN(parsed.getTime()) ? new Date(str) : parsed;
}

/**
 * Formats a comment timestamp into a compact, human-readable string.
 *
 * Rules:
 *  - < 1 min  → "just now"
 *  - < 60 min → "X min ago"
 *  - < 24 hrs → "Xh ago"
 *  - < 7 days → "Xd ago"
 *  - Same year → "Jul 29"
 *  - Older    → "Jul 29, 2025"
 *
 * The backend stores datetimes in UTC without a timezone suffix.
 * We append "Z" if the string has no offset so Date parses it correctly.
 */
export function formatCommentTime(dateStr: string): string {
  const date = parseUtcDate(dateStr) ?? new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHrs = Math.floor(diffMin / 60);
  const diffDays = Math.floor(diffHrs / 24);

  if (diffSec < 60) return "just now";
  if (diffMin < 60) return `${diffMin} min ago`;
  if (diffHrs < 24) return `${diffHrs}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  const sameYear = date.getFullYear() === now.getFullYear();
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    ...(sameYear ? {} : { year: "numeric" }),
  });
}

/**
 * Calculates the bearing between two points [lng, lat] in degrees.
 * Returns a value between 0 and 360.
 */
export function getBearing(start: [number, number], end: [number, number]): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const toDeg = (rad: number) => (rad * 180) / Math.PI;

  const lon1 = toRad(start[0]);
  const lat1 = toRad(start[1]);
  const lon2 = toRad(end[0]);
  const lat2 = toRad(end[1]);

  const y = Math.sin(lon2 - lon1) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(lon2 - lon1);
  const brng = toDeg(Math.atan2(y, x));
  return Math.round((brng + 360) % 360);
}

/**
 * Automatically converts a name to proper name casing (Title Case).
 * Capitalizes the first letter of each word/token while lowercasing the rest.
 * Correctly handles spaces, hyphens, apostrophes, and accented/Unicode characters.
 * E.g., "juan dela cruz" -> "Juan Dela Cruz", "MARY-JANE" -> "Mary-Jane", "o'connor" -> "O'Connor"
 */
export function toNameCase(name: string): string {
  if (!name) return "";
  return name.replace(/\p{L}+/gu, (word) => {
    return word.charAt(0).toLocaleUpperCase() + word.slice(1).toLocaleLowerCase();
  });
}

