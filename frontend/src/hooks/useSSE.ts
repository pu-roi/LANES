import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";

const getSseUrl = (): string => {
  if (typeof window === "undefined") return "";
  
  const apiEnv = process.env.NEXT_PUBLIC_API_URL;
  if (apiEnv && apiEnv.startsWith("http")) {
    return `${apiEnv}/sse/stream`;
  }
  
  if (window.location.port === "3000") {
    return `http://${window.location.hostname}:8000/api/v1/sse/stream`;
  }
  
  return `/api/v1/sse/stream`;
};

export function useSSE() {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (typeof window === "undefined") return;

    const sseUrl = getSseUrl();
    console.log(`Connecting to SSE at: ${sseUrl}`);
    
    const eventSource = new EventSource(sseUrl);

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
      console.error("SSE encountered an error, EventSource will automatically attempt to reconnect:", err);
    };

    return () => {
      eventSource.close();
    };
  }, [queryClient]);
}
