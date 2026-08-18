import { useEffect, useRef } from 'react';
import { saveFloodsOffline } from '@/lib/offline/storage';
import { useQueryClient } from '@tanstack/react-query';

export function useLiveSync() {
  const queryClient = useQueryClient();
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // Only connect if the browser supports EventSource
    if (typeof window === 'undefined' || !window.EventSource) return;

    // Connect to the FastAPI SSE endpoint
    // In production, this should point to your real backend domain
    const sseUrl = 'http://localhost:8000/api/v1/sync/stream';
    const source = new EventSource(sseUrl);
    eventSourceRef.current = source;

    source.addEventListener('init', async (event) => {
      try {
        const floods = JSON.parse(event.data);
        await saveFloodsOffline(floods);
        // Optionally update the react-query cache so the map updates instantly
        // queryClient.setQueryData(['floods'], floods);
      } catch (err) {
        console.error("Failed to parse SSE init:", err);
      }
    });

    source.addEventListener('update', async (event) => {
      try {
        const floods = JSON.parse(event.data);
        await saveFloodsOffline(floods);
        // Update the cache so useFloodZonesLayer instantly rerenders
        // We use queryClient.invalidateQueries to trigger a background refetch
        // or we can set it directly if the data structure matches perfectly.
        // For safety, let's just tell react-query to refetch the regular endpoint:
        queryClient.invalidateQueries({ queryKey: ['reports', 'flood'] });
      } catch (err) {
        console.error("Failed to parse SSE update:", err);
      }
    });

    source.onerror = (err) => {
      console.error("SSE Connection Error. Retrying automatically...", err);
    };

    return () => {
      if (source.readyState === 1) { // OPEN
        source.close();
      }
    };
  }, [queryClient]);
}
