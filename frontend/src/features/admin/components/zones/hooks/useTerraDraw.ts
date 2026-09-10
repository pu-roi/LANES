"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  TerraDraw,
  TerraDrawPolygonMode,
  TerraDrawRectangleMode,
  TerraDrawCircleMode,
  TerraDrawFreehandMode,
} from "terra-draw";
import { TerraDrawMapLibreGLAdapter } from "terra-draw-maplibre-gl-adapter";
import type { GeometryMode, Severity } from "../types";
import { getTerraDrawActiveZoneStyles } from "../types";
import type { ReportGeometry } from "@/features/admin/adminApi";

interface UseTerraDrawOptions {
  mapInstance: any;
  geometryMode: GeometryMode;
  severity: Severity;
  isEnabled?: boolean;
  isInteractive?: boolean;
}

export function useTerraDraw({
  mapInstance,
  geometryMode,
  severity,
  isEnabled = true,
  isInteractive = isEnabled,
}: UseTerraDrawOptions) {
  const drawRef = useRef<TerraDraw | null>(null);
  const [drawInstance, setDrawInstance] = useState<TerraDraw | null>(null);
  const [drawnGeometry, setDrawnGeometry] = useState<ReportGeometry | null>(null);
  const [drawnFeatures, setDrawnFeatures] = useState<any[]>([]);
  const [isDrawingMode, setIsDrawingMode] = useState(false);

  const resetMapCursor = useCallback(() => {
    const canvas = mapInstance?.getCanvas?.();
    const container = mapInstance?.getCanvasContainer?.();
    if (canvas) canvas.style.cursor = "";
    if (container) container.style.cursor = "";
  }, [mapInstance]);

  // Initialize TerraDraw
  useEffect(() => {
    if (!mapInstance || !isEnabled) return;
    if (drawRef.current) return;

    const initDraw = () => {
      try {
        const adapter = new TerraDrawMapLibreGLAdapter({ map: mapInstance });
        const initialStyles = getTerraDrawActiveZoneStyles(severity);

        const draw = new TerraDraw({
          adapter,
          modes: [
            new TerraDrawPolygonMode({ pointerDistance: 45, styles: initialStyles as any }),
            new TerraDrawFreehandMode({ pointerDistance: 45, styles: initialStyles as any }),
            new TerraDrawRectangleMode({ pointerDistance: 45, styles: initialStyles as any }),
            new TerraDrawCircleMode({ pointerDistance: 45, styles: initialStyles as any }),
          ],
        });

        draw.start();
        drawRef.current = draw;
        setDrawInstance(draw);

        // Listen for drawing changes
        draw.on("change", () => {
          const snapshot = draw.getSnapshot();
          setDrawnFeatures(snapshot);
          if (snapshot.length === 1) {
            setDrawnGeometry(snapshot[0].geometry as any);
          } else if (snapshot.length > 1) {
            const multiPolyCoords = snapshot
              .map((f: any) => f.geometry?.coordinates)
              .filter(Boolean);
            setDrawnGeometry({
              type: "MultiPolygon",
              coordinates: multiPolyCoords,
            } as any);
          } else {
            setDrawnGeometry(null);
          }
        });
      } catch (err) {
        console.warn("Failed to initialize TerraDraw:", err);
      }
    };

    let initTimer: NodeJS.Timeout | null = null;
    initTimer = setTimeout(() => {
      if (mapInstance.isStyleLoaded && mapInstance.isStyleLoaded()) {
        initDraw();
      } else if (mapInstance.once) {
        mapInstance.once("style.load", initDraw);
      }
    }, 360);

    return () => {
      if (initTimer) clearTimeout(initTimer);
      if (drawRef.current) {
        try {
          if (drawRef.current.enabled && mapInstance?.getStyle && mapInstance.getStyle()) {
            drawRef.current.stop();
          }
        } catch {}
        drawRef.current = null;
        setDrawInstance(null);
      }
      resetMapCursor();
    };
  }, [mapInstance, isEnabled, resetMapCursor]);

  // Sync mode changes
  useEffect(() => {
    if (!drawRef.current) return;
    try {
      if (!isInteractive || geometryMode === "line") {
        drawRef.current.setMode("static");
        setIsDrawingMode(false);
        resetMapCursor();
      } else {
        drawRef.current.setMode(geometryMode);
        setIsDrawingMode(true);
      }
    } catch (err) {
      console.warn("Error setting TerraDraw mode:", err);
    }
  }, [geometryMode, drawInstance, isInteractive, resetMapCursor]);

  // Sync styles on severity change
  useEffect(() => {
    if (!drawRef.current) return;
    const styles = getTerraDrawActiveZoneStyles(severity);
    try {
      const modes = ["polygon", "freehand", "rectangle", "circle"] as const;
      modes.forEach((modeName) => {
        const mode = (drawRef.current as any)?._modes?.[modeName];
        if (mode && typeof mode.updateStyles === "function") {
          mode.updateStyles(styles);
        }
      });
    } catch (err) {
      console.warn("Error updating TerraDraw styles:", err);
    }
  }, [severity]);

  // Clear features helper
  const clearDrawing = useCallback(() => {
    if (drawRef.current) {
      try {
        drawRef.current.clear();
      } catch (err) {
        console.warn("Failed to clear features:", err);
      }
    }
    setDrawnFeatures([]);
    setDrawnGeometry(null);
  }, []);

  const restoreDrawing = useCallback((features: any[]) => {
    if (!drawRef.current) return false;
    try {
      drawRef.current.clear();
      if (features.length > 0) {
        drawRef.current.addFeatures(features);
      }
      const snapshot = drawRef.current.getSnapshot();
      setDrawnFeatures(snapshot);
      if (snapshot.length === 1) {
        setDrawnGeometry(snapshot[0].geometry as ReportGeometry);
      } else if (snapshot.length > 1) {
        setDrawnGeometry({
          type: "MultiPolygon",
          coordinates: snapshot.map((feature: any) => feature.geometry?.coordinates).filter(Boolean),
        } as ReportGeometry);
      } else {
        setDrawnGeometry(null);
      }
      return true;
    } catch (err) {
      console.error("Failed to restore zone drawing", err);
      return false;
    }
  }, []);

  const cancelDrawingMode = useCallback(() => {
    if (drawRef.current) {
      try {
        drawRef.current.setMode("static");
      } catch {}
    }
    resetMapCursor();
    setIsDrawingMode(false);
  }, [resetMapCursor]);

  return {
    drawInstance,
    drawnGeometry,
    drawnFeatures,
    isDrawingMode,
    clearDrawing,
    restoreDrawing,
    cancelDrawingMode,
    setDrawnGeometry,
  };
}
