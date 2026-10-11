import type { ReportGeometry } from "../adminApi";

/** A shared-coordinate drawing avoids allocating a second WebGL map in the dialog. */
export function ZoneGeometryComparison({ official, proposal }: { official: ReportGeometry; proposal?: ReportGeometry | null }) {
  const paths = (geometry: ReportGeometry | null | undefined): [number, number][][] => {
    if (!geometry) return [];
    switch (geometry.type) {
      case "Point": return [[geometry.coordinates]];
      case "LineString": return [geometry.coordinates];
      case "MultiLineString": case "Polygon": return geometry.coordinates;
      case "MultiPolygon": return geometry.coordinates.flat();
    }
  };
  const officialPaths = paths(official), proposalPaths = paths(proposal);
  const points = [...officialPaths, ...proposalPaths].flat();
  if (!points.length) return <p className="text-sm text-slate-500">No geometry to compare.</p>;
  const lng = points.map(point => point[0]), lat = points.map(point => point[1]);
  const minX = Math.min(...lng), minY = Math.min(...lat);
  const spanX = Math.max(...lng) - minX || 0.00001, spanY = Math.max(...lat) - minY || 0.00001;
  const longitudeScale = Math.cos((minY * Math.PI) / 180);
  const scale = Math.min(440 / (spanX * longitudeScale), 170 / spanY);
  const project = ([x, y]: [number, number]) => `${30 + (x - minX) * longitudeScale * scale},${200 - (y - minY) * scale}`;
  return <figure className="space-y-2">
    <figcaption className="text-xs font-semibold text-slate-500">Boundary comparison · north up</figcaption>
    <svg viewBox="0 0 500 230" role="img" aria-label="Current official boundary in blue and submitted road extent in orange" className="w-full rounded-lg bg-slate-50">
      {officialPaths.map((line, index) => <polyline key={`official-${index}`} points={line.map(project).join(" ")} fill={official.type.includes("Polygon") ? "#dbeafe" : "none"} stroke="#2563eb" strokeWidth="3" />)}
      {proposalPaths.map((line, index) => <polyline key={`proposal-${index}`} points={line.map(project).join(" ")} fill="none" stroke="#ea580c" strokeWidth="4" strokeDasharray="8 5" />)}
      <text x="470" y="22" className="fill-slate-500 text-xs">N ↑</text>
    </svg>
    <div className="flex flex-wrap gap-4 text-xs"><span className="font-semibold text-blue-700">Blue: official zone</span><span className="font-semibold text-orange-700">Orange dashed: submitted road</span></div>
    <p className="text-xs leading-5 text-slate-500">Geometry comparison without a basemap. A submitted road is evidence; verify its full extent on the map before publishing.</p>
  </figure>;
}
