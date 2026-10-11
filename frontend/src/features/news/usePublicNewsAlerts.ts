"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { publicNewsApi } from "./publicNewsApi";

export function usePublicNewsAlerts(page: number, enabled: boolean) {
  const [offline, setOffline] = useState(false);
  useEffect(() => {
    const update = () => setOffline(!navigator.onLine);
    update();
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);
  const query = useQuery({
    queryKey: ["publicNewsAlerts", page],
    queryFn: ({ signal }) => publicNewsApi.list(page, signal),
    enabled,
    retry: false,
    staleTime: 25_000,
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
    refetchOnReconnect: "always",
  });
  // Cached observations are useful context, but only the server projects status.
  return { ...query, offline, currentStatusUnavailable: offline || query.isError || query.isStale || query.isFetching };
}
