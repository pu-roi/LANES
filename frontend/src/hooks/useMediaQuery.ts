import { useCallback, useSyncExternalStore } from "react";

export function useMediaQuery(query: string): boolean {
  const subscribe = useCallback((notify: () => void) => {
    const media = window.matchMedia(query);
    if (media.addEventListener) {
      media.addEventListener("change", notify);
    } else {
      media.addListener(notify);
    }

    return () => {
      if (media.removeEventListener) {
        media.removeEventListener("change", notify);
      } else {
        media.removeListener(notify);
      }
    };
  }, [query]);

  const getSnapshot = useCallback(() => window.matchMedia(query).matches, [query]);
  // Hydrate the server layout first, then subscribe to the actual viewport.
  return useSyncExternalStore(subscribe, getSnapshot, () => false);
}
