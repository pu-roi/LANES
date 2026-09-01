import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
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
  // Ensure UTC parsing — append Z if no timezone info present
  const utcStr =
    dateStr.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(dateStr)
      ? dateStr
      : dateStr + "Z";

  const date = new Date(utcStr);
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
