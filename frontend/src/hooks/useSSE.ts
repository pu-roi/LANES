import { useEffect, useRef, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getSseUrl } from "@/lib/sse";

const INITIAL_BACKOFF_MS = 1000;
const MAX_BACKOFF_MS = 30000;
const MAX_RETRIES = 20;

export function useSSE() {
  const queryClient = useQueryClient();
  const eventSourceRef = useRef<EventSource | null>(null);
  const backoffRef = useRef(INITIAL_BACKOFF_MS);
  const retriesRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    if (typeof window === "undefined") return;

    const sseUrl = getSseUrl("/sse/stream");
    console.log(`Connecting to SSE at: ${sseUrl}`);

    const eventSource = new EventSource(sseUrl, { withCredentials: true });
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log("SSE connected successfully");
      // Connection succeeded — reset backoff
      backoffRef.current = INITIAL_BACKOFF_MS;
      retriesRef.current = 0;
    };

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        console.log("Received SSE event:", payload);

        const { event: eventName } = payload;
        if (eventName === "report_approved" || eventName === "report_rejected") {
          queryClient.invalidateQueries({ queryKey: ["adminReports"] });
          queryClient.invalidateQueries({ queryKey: ["activeZones"] });
          queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
        } else if (eventName === "zone_deactivated") {
          queryClient.invalidateQueries({ queryKey: ["adminZones"] });
          queryClient.invalidateQueries({ queryKey: ["activeZones"] });
          queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
        } else if (eventName === "report_created") {
          queryClient.invalidateQueries({ queryKey: ["adminReports"] });
          queryClient.invalidateQueries({ queryKey: ["adminDashboardStats"] });
        }
      } catch (err) {
        console.warn("Failed to parse SSE message:", err);
      }
    };

    eventSource.onerror = () => {
      // Close the broken connection to prevent native auto-reconnect
      eventSource.close();
      eventSourceRef.current = null;

      if (!mountedRef.current) return;

      if (retriesRef.current >= MAX_RETRIES) {
        console.error(`SSE: max retries (${MAX_RETRIES}) reached. Giving up.`);
        return;
      }

      const delay = backoffRef.current;
      console.warn(`SSE: reconnecting in ${delay}ms (attempt ${retriesRef.current + 1}/${MAX_RETRIES})`);

      reconnectTimerRef.current = setTimeout(() => {
        retriesRef.current += 1;
        backoffRef.current = Math.min(backoffRef.current * 2, MAX_BACKOFF_MS);
        connect();
      }, delay);
    };
  }, [queryClient]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [connect]);
}
