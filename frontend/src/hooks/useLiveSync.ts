import { useEffect, useRef } from 'react';
import { saveFloodsOffline } from '@/lib/offline/storage';
import { useQueryClient } from '@tanstack/react-query';
import { getSseUrl } from '@/lib/sse';

export function useLiveSync() {
  const queryClient = useQueryClient();
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // Only connect if the browser supports EventSource
    if (typeof window === 'undefined' || !window.EventSource) return;

    const sseUrl = getSseUrl('/sync/stream');
    let source: EventSource | null = null;

    try {
      source = new EventSource(sseUrl);
      eventSourceRef.current = source;

      source.addEventListener('init', async (event) => {
        try {
          const floods = JSON.parse(event.data);
          await saveFloodsOffline(floods);
        } catch (err) {
          console.warn("Failed to parse SSE init:", err);
        }
      });

      source.addEventListener('update', async (event) => {
        try {
          const floods = JSON.parse(event.data);
          await saveFloodsOffline(floods);
          queryClient.invalidateQueries({ queryKey: ['reports', 'flood'] });
        } catch (err) {
          console.warn("Failed to parse SSE update:", err);
        }
      });

      source.onerror = (err) => {
        // EventSource automatically reconnects; log warning rather than noisy error
        console.warn("Live sync SSE connection state changed, retrying automatically...", err);
      };
    } catch (err) {
      console.warn("Failed to initialize LiveSync EventSource:", err);
    }

    return () => {
      if (source) {
        source.close();
      }
      if (eventSourceRef.current === source) {
        eventSourceRef.current = null;
      }
    };
  }, [queryClient]);
}
