"use client";

import { useState, useCallback } from "react";
import type { ZoneDraftItem } from "../types";

export function useZoneDrafts() {
  const [drafts, setDrafts] = useState<ZoneDraftItem[]>([]);

  const addDraft = useCallback((draft: ZoneDraftItem) => {
    setDrafts((prev) => [...prev, draft]);
  }, []);

  const removeDraft = useCallback((id: string) => {
    setDrafts((prev) => prev.filter((d) => d.id !== id));
  }, []);

  const clearDrafts = useCallback(() => {
    setDrafts([]);
  }, []);

  return {
    drafts,
    addDraft,
    removeDraft,
    clearDrafts,
    setDrafts,
  };
}
