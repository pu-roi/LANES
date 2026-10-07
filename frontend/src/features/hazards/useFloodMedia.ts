"use client";
import { useCallback, useEffect, useRef, useState } from "react";
export function useFloodMedia() {
  const [mediaFiles, setMediaFiles] = useState<File[]>([]);
  const mediaPreviewUrlsRef = useRef(new WeakMap<File, string>());
  const createdPreviewUrlsRef = useRef(new Set<string>());
  const getImagePreviewUrl = useCallback((file: File) => {
    if (!file.type.startsWith("image/")) return undefined;
    const existingUrl = mediaPreviewUrlsRef.current.get(file);
    if (existingUrl) return existingUrl;

    const previewUrl = URL.createObjectURL(file);
    mediaPreviewUrlsRef.current.set(file, previewUrl);
    createdPreviewUrlsRef.current.add(previewUrl);
    return previewUrl;
  }, []);

  const removeMediaFile = useCallback((index: number) => {
    setMediaFiles((current) => {
      const file = current[index];
      const previewUrl = file ? mediaPreviewUrlsRef.current.get(file) : undefined;
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
        createdPreviewUrlsRef.current.delete(previewUrl);
        mediaPreviewUrlsRef.current.delete(file);
      }
      return current.filter((_, fileIndex) => fileIndex !== index);
    });
  }, []);

  const clearMediaFiles = useCallback(() => {
    createdPreviewUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
    createdPreviewUrlsRef.current.clear();
    mediaPreviewUrlsRef.current = new WeakMap<File, string>();
    setMediaFiles([]);
  }, []);

  useEffect(() => () => {
    createdPreviewUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
    createdPreviewUrlsRef.current.clear();
  }, []);

  return { mediaFiles, setMediaFiles, getImagePreviewUrl, removeMediaFile, clearMediaFiles };
}
