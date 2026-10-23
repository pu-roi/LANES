export interface HistoricalNewsMetadata {
  schema_version: "historical-import-v1";
  dataset_id: string;
  disposition: "historical_archive" | "active_demo";
  label: string;
  occurrence_date: string | null;
  observed_at: string | null;
  precision: "instant" | "date" | "unknown";
  closure_basis: string;
  simulated_interval_minutes: number | null;
  imported_at: string;
  source_url: string;
  source_publisher: string;
  source_excerpt: string;
  article_id: number;
  run_id: number;
  group_id: string;
}
