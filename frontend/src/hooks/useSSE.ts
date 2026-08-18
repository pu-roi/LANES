import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

const getSseUrl = (): string => {
  if (typeof window === "undefined") return "";
  
  const apiEnv = process.env.NEXT_PUBLIC_API_URL;
  if (apiEnv && apiEnv.startsWith("http")) {
    return `${apiEnv}/sse/stream`;
  }
  
  // In local development, bypass the Next.js proxy which often buffers SSE.
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.hostname.startsWith('192.168.') || window.location.hostname.startsWith('10.')) {
    const host = window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname;
    return `http://${host}:8000/api/v1/sse/stream`;
  }
  
  return `/api/v1/sse/stream`;
};

export function useSSE() {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (typeof window === "undefined") return;

    const sseUrl = getSseUrl();
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
