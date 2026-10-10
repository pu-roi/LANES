import { apiClient } from "@/lib/apiClient";

export interface LocalNewsArticle {
  id: number;
  title: string;
  publisher: string;
  source_url: string;
  published_at: string;
}

export interface LocalNewsUpdates {
  items: LocalNewsArticle[];
  as_of: string;
}

export function getLocalNewsUpdates(signal?: AbortSignal) {
  return apiClient.get<LocalNewsUpdates>("/news/local-updates?limit=5", { signal, cache: "no-store" });
}
