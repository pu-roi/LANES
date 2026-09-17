import { useEffect, useRef, useCallback } from 'react';
import { saveFloodsOffline } from '@/lib/offline/storage';
import { useQueryClient } from '@tanstack/react-query';
import { getSseUrl } from '@/lib/sse';

const INITIAL_BACKOFF_MS = 1000;
const MAX_BACKOFF_MS = 30000;
const MAX_RETRIES = 20;

export function useLiveSync() {
  const queryClient = useQueryClient();
  const eventSourceRef = useRef<EventSource | null>(null);
  const backoffRef = useRef(INITIAL_BACKOFF_MS);
  const retriesRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
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

      source.onopen = () => {
        // Connection succeeded — reset backoff
        backoffRef.current = INITIAL_BACKOFF_MS;
        retriesRef.current = 0;
      };

      source.onerror = () => {
        // Close the broken connection to prevent native auto-reconnect
        source?.close();
        eventSourceRef.current = null;

        if (!mountedRef.current) return;

        if (retriesRef.current >= MAX_RETRIES) {
          console.error(`LiveSync: max retries (${MAX_RETRIES}) reached. Giving up.`);
          return;
        }

        const delay = backoffRef.current;
        console.warn(`LiveSync: reconnecting in ${delay}ms (attempt ${retriesRef.current + 1}/${MAX_RETRIES})`);

        reconnectTimerRef.current = setTimeout(() => {
          retriesRef.current += 1;
          backoffRef.current = Math.min(backoffRef.current * 2, MAX_BACKOFF_MS);
          connect();
        }, delay);
      };
    } catch (err) {
      console.warn("Failed to initialize LiveSync EventSource:", err);
    }
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
