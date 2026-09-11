import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getSseUrl } from "@/lib/sse";

export function useSSE() {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (typeof window === "undefined") return;

    const sseUrl = getSseUrl("/sse/stream");
    console.log(`Connecting to SSE at: ${sseUrl}`);
    
    const eventSource = new EventSource(sseUrl, { withCredentials: true });

    eventSource.onopen = () => {
      console.log("SSE connected successfully");
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

    eventSource.onerror = (err) => {
      // EventSource automatically reconnects when the connection is dropped or backend restarts.
      console.warn("SSE connection state changed, attempting automatic reconnect...", err);
    };

    return () => {
      eventSource.close();
    };
  }, [queryClient]);
}
