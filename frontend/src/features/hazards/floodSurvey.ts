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
