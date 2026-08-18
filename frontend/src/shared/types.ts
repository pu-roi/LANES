// Strictly typed schemas mirroring the FastAPI Pydantic Models
// To comply with STANDARDS.md, we avoid `any` types

export interface FloodReport {
  id: number;
  raw_text: string;
  source: string;
  severity: "low" | "medium" | "high" | "extreme";
  status: "Pending" | "Approved" | "Rejected";
  human_readable_location?: string;
  barangay?: string;
  is_public: boolean;
  geometry: any;
  media_urls: string[];
  location_confidence: number;
  severity_confidence: number;
  created_at: string;
  updated_at: string;
}

export interface RouteResponse {
  route_id: string;
  distance_meters: number;
  geometry: any; // GeoJSON
  safe: boolean;
}
