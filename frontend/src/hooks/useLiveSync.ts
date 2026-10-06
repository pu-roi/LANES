import { useEffect, useRef, useCallback } from 'react';
import { saveFloodsOffline } from '@/lib/offline/storage';
import { useQueryClient } from '@tanstack/react-query';
import { getSseUrl } from '@/lib/sse';
import { useToast } from '@/shared/ui/feedback/Toast';

const INITIAL_BACKOFF_MS = 1000;
const MAX_BACKOFF_MS = 30000;
const MAX_RETRIES = 20;

export function useLiveSync() {
  const queryClient = useQueryClient();
  const { error: showError } = useToast();
  const previousSnapshotRef = useRef<string | null>(null);
  const failureReportedRef = useRef(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const backoffRef = useRef(INITIAL_BACKOFF_MS);
  const retriesRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const connect = useCallback(function connect() {
    if (!mountedRef.current) return;
    if (typeof window === 'undefined' || !window.EventSource) return;

    const sseUrl = getSseUrl('/sync/stream');
    let source: EventSource | null = null;

    try {
      source = new EventSource(sseUrl);
      eventSourceRef.current = source;

      const receiveSnapshot = async (event: MessageEvent, isUpdate: boolean) => {
        try {
          if (event.data === previousSnapshotRef.current) return;
          const floods = JSON.parse(event.data);
          if (!Array.isArray(floods)) throw new Error('Invalid live flood snapshot');
          const hadSnapshot = previousSnapshotRef.current !== null;
          await saveFloodsOffline(floods);
          previousSnapshotRef.current = event.data;
          failureReportedRef.current = false;
          // Reconnecting must also recover changes missed while disconnected.
          if (isUpdate || hadSnapshot) {
            void queryClient.invalidateQueries({ queryKey: ['reports', 'flood'] });
            void queryClient.invalidateQueries({ queryKey: ['activeZones'] });
            void queryClient.invalidateQueries({ queryKey: ['activeZonesMap'] });
            void queryClient.invalidateQueries({ queryKey: ['adminZones'] });
            void queryClient.invalidateQueries({ queryKey: ['publicNewsAlerts'] });
          }
        } catch (err) {
          console.warn('Failed to save live flood snapshot:', err);
          if (!failureReportedRef.current) {
            showError('Live flood sync unavailable', 'Could not save the latest flood data. The map will continue checking for updates.');
            failureReportedRef.current = true;
          }
        }
      };

      source.addEventListener('init', (event) => { void receiveSnapshot(event, false); });
      source.addEventListener('update', (event) => { void receiveSnapshot(event, true); });
      source.addEventListener('keepalive', (event) => {
        try {
          const status = JSON.parse(event.data).status;
          if (status === 'unchanged') failureReportedRef.current = false;
          if (status === 'pool_busy' && !failureReportedRef.current) {
            showError('Live flood status unavailable', 'Could not refresh live flood data. Cached data may be out of date.');
            failureReportedRef.current = true;
          }
        } catch {
          showError('Live flood sync unavailable', 'An invalid live update was received. The map will continue checking for updates.');
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
          showError('Live flood sync disconnected', 'Live sync could not reconnect. The map will continue checking for updates.');
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
      showError('Live flood sync unavailable', 'The map will continue checking for updates.');
    }
  }, [queryClient, showError]);

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
