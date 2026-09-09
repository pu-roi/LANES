"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import type { ZoneDraftItem } from "../types";

const STORAGE_KEY = "lanes_admin_zone_drafts";

export function useZoneDrafts() {
  const [drafts, setDrafts] = useState<ZoneDraftItem[]>([]);
  const hasHydrated = useRef(false);

  // Hydrate from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) {
          setDrafts(parsed);
        }
      }
    } catch (err) {
      console.warn("Failed to hydrate zone drafts:", err);
    } finally {
      hasHydrated.current = true;
    }
  }, []);

  // Save to localStorage on change
  useEffect(() => {
    if (!hasHydrated.current) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(drafts));
    } catch (err) {
      console.warn("Failed to persist zone drafts:", err);
    }
  }, [drafts]);

  const addDraft = useCallback((draft: ZoneDraftItem) => {
    setDrafts((prev) => [...prev, draft]);
  }, []);

  const removeDraft = useCallback((id: string) => {
    setDrafts((prev) => prev.filter((d) => d.id !== id));
  }, []);

  const clearDrafts = useCallback(() => {
    setDrafts([]);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {}
  }, []);

  return {
    drafts,
    addDraft,
    removeDraft,
    clearDrafts,
    setDrafts,
  };
}
