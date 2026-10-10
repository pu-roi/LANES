"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/apiClient";
import type { PlacementEnvelope } from "@/features/admin/review/reviewApi";
import { getLocalNewsSimulation } from "@/lib/localNewsSimulation";

export interface NewsSimulation {
  mode: "september24";
  simulated_at: string;
  article_title: string;
  source_url: string;
  reported_locations: number;
  status: "Needs Review";
  placement: PlacementEnvelope | null;
  modeled_candidates: number;
  routing_affected: false;
  reason: string;
  subsidence_reason: string;
}

export function useNewsSimulation() {
  const mode = useQuery({ queryKey: ["local-news-simulation-mode"], queryFn: getLocalNewsSimulation,
    staleTime: Infinity, retry: false });
  const query = useQuery({ queryKey: ["news-simulation"],
    queryFn: ({ signal }) => apiClient.get<NewsSimulation>("/news/simulation", { signal, cache: "no-store" }),
    enabled: mode.data === "september24", retry: false, staleTime: 30_000 });
  return { ...query, enabled: mode.data === "september24", ready: !mode.isPending,
    configurationError: mode.isError ? mode.error.message : null };
}
