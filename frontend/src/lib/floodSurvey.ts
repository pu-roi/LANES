/** Canonical survey vocabulary shared with official zone editors. */
export const VEHICLE_OPTIONS = [
  { id: "walk", label: "Pedestrians" }, { id: "bicycle", label: "Bicycles / E-Bikes" },
  { id: "motorcycle", label: "Motorcycles" }, { id: "light", label: "Sedans / Hatchbacks" },
  { id: "suv", label: "SUVs / Pickups" }, { id: "heavy", label: "Large Trucks / Buses" },
];
export const HAZARD_OPTIONS = [
  { value: "yes", label: "Yes", activeClass: "bg-red-50 border-red-300 text-red-700" },
  { value: "no", label: "No", activeClass: "bg-green-50 border-green-300 text-green-700" },
  { value: "unsure", label: "Unsure", activeClass: "bg-gray-100 border-gray-300 text-gray-700" },
];

/** Display canonical IDs and legacy display labels without changing stored values. */
export function formatPassableVehicles(value: string | string[] | null | undefined): string {
  if (value == null) return "Not recorded";
  const values = Array.isArray(value) ? value : value.split(",");
  if (!values.length || (values.length === 1 && !values[0].trim())) return "None observed";
  return values.map(item => {
    const clean = item.trim();
    return VEHICLE_OPTIONS.find(option => option.id.toLowerCase() === clean.toLowerCase() || option.label.toLowerCase() === clean.toLowerCase())?.label ?? clean.replaceAll("_", " ");
  }).join(", ");
}
export function formatHazards(value: string | null | undefined): string {
  if (!value) return "Not recorded";
  return HAZARD_OPTIONS.find(option => option.value === value.toLowerCase())?.label ?? value;
}
