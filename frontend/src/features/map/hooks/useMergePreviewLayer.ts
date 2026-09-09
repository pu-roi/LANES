import { useEffect } from "react";
import type { Map } from "maplibre-gl";
import type { FloodReport, MergeCandidateItem, ReportGeometry } from "@/features/admin/adminApi";

interface UseMergePreviewLayerProps {
  map: Map | null;
  isLoaded: boolean;
  isOpen: boolean;
  primaryReport: FloodReport | null;
  selectedCandidates: MergeCandidateItem[];
  proposedGeometry?: ReportGeometry | null;
}

const CANDIDATE_COLORS = ["#3b82f6", "#8b5cf6", "#ec4899", "#f97316", "#06b6d4"];

export function useMergePreviewLayer({
  map,
  isLoaded,
  isOpen,
  primaryReport,
  selectedCandidates,
  proposedGeometry,
}: UseMergePreviewLayerProps) {
  useEffect(() => {
    if (!map || !isLoaded) return;

    const sourceId = "merge-preview-source";
    const lineLayerId = "merge-preview-lines";
    const fillLayerId = "merge-preview-polygons";

    const existingSource = map.getSource(sourceId) as any;

    if (!isOpen || !primaryReport) {
      if (existingSource) {
        existingSource.setData({ type: "FeatureCollection", features: [] });
      }
      return;
    }

    const features: any[] = [];

    // 1. Primary Report Geometry
    if (primaryReport.geometry) {
      features.push({
        type: "Feature",
        properties: {
          color: "#2563eb", // Deep primary blue
          is_primary: true,
          label: `Primary #${primaryReport.id}`,
        },
        geometry: primaryReport.geometry,
      });
    }

    // 2. Candidate Report Geometries (each with a distinct vibrant color)
    selectedCandidates.forEach((cand, idx) => {
      if (cand.geometry) {
        features.push({
          type: "Feature",
          properties: {
            color: CANDIDATE_COLORS[idx % CANDIDATE_COLORS.length],
            is_primary: false,
            label: `Candidate #${cand.report_id}`,
          },
          geometry: cand.geometry,
        });
      }
    });

    // 3. Proposed Merged Geometry (pulsing dashed preview)
    if (proposedGeometry) {
      features.push({
        type: "Feature",
        properties: {
          color: "#10b981", // Emerald green
          is_proposed: true,
          label: "Proposed Merged Zone",
        },
        geometry: proposedGeometry,
      });
    }

    const featureCollection: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features,
    };

    if (existingSource) {
      existingSource.setData(featureCollection);
    } else {
      if (!map.getStyle()) return;

      map.addSource(sourceId, {
        type: "geojson",
        data: featureCollection,
      });

      // Polygon fills (for drawn shapes or proposed buffers)
      map.addLayer({
        id: fillLayerId,
        type: "fill",
        source: sourceId,
        filter: ["==", "$type", "Polygon"],
        paint: {
          "fill-color": ["get", "color"],
          "fill-opacity": 0.25,
        },
      });

      // Line strokes
      map.addLayer({
        id: lineLayerId,
        type: "line",
        source: sourceId,
        filter: ["in", "$type", "LineString", "Polygon"],
        paint: {
          "line-color": ["get", "color"],
          "line-width": [
            "case",
            ["get", "is_proposed"], 6,
            ["get", "is_primary"], 4,
            3
          ],
          "line-dasharray": [
            "case",
            ["get", "is_proposed"], ["literal", [2, 1]],
            ["literal", [1, 0]]
          ],
          "line-opacity": 0.85,
        },
      });
    }

    return () => {
      // Clean up source data on unmount
      const src = map.getSource(sourceId) as any;
      if (src) {
        src.setData({ type: "FeatureCollection", features: [] });
      }
    };
  }, [map, isLoaded, isOpen, primaryReport, selectedCandidates, proposedGeometry]);
}
