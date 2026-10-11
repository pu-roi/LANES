export const PHILIPPINE_LOCATIONS: Record<string, Record<string, string[]>> = {
  "Metro Manila": {
    "Pasig": [
      "Bagong Ilog", "Bagong Katipunan", "Bambang", "Buting", "Caniogan", 
      "Dela Paz", "Kalawaan", "Kapasigan", "Kapitolyo", "Malinao", 
      "Manggahan", "Maybunga", "Oranbo", "Palatiw", "Pinagbuhatan", 
      "Pineda", "Rosario", "Sagad", "San Antonio", "San Joaquin", 
      "San Jose", "San Nicolas", "Santa Cruz", "Santa Lucia", "Santa Rosa", 
      "Santo Tomas", "Santolan", "Sumilang", "Ugong"
    ],
    "Quezon City": [
      "Bagumbayan", "Batasan Hills", "Commonwealth", "Cubao", "Diliman",
      "Fairview", "Holy Spirit", "Kamuning", "Loyola Heights", "Matandang Balara",
      "Novaliches Proper", "Payatas", "Project 4", "Project 6", "San Bartolome",
      "Tandang Sora", "UP Campus"
    ],
    "Manila": [
      "Binondo", "Ermita", "Intramuros", "Malate", "Paco",
      "Pandacan", "Port Area", "Quiapo", "Sampaloc", "San Andres",
      "San Miguel", "San Nicolas", "Santa Ana", "Santa Cruz", "Tondo"
    ],
    "Makati": [
      "Bangkal", "Bel-Air", "Carmona", "Cembo", "Comembo",
      "Dasmariñas", "East Rembo", "Forbes Park", "Guadalupe Nuevo", "Guadalupe Viejo",
      "Kasilawan", "La Paz", "Magallanes", "Olympia", "Palanan",
      "Pembo", "Pinagkaisahan", "Pio del Pilar", "Pitogo", "Poblacion",
      "Post Proper Northside", "Post Proper Southside", "Rizal", "San Antonio", "San Isidro",
      "San Lorenzo", "Santa Cruz", "Singkamas", "South Cembo", "Tejeros",
      "Urdaneta", "Valenzuela", "West Rembo"
    ],
    "Marikina": [
      "Barangka", "Calumpang", "Concepcion Uno", "Concepcion Dos", "Fortune",
      "Industrial Valley", "Jesus Dela Peña", "Malanday", "Marikina Heights", "Nangka",
      "Parang", "San Roque", "Santa Elena", "Santo Niño", "Tañong", "Tumana"
    ],
    "Taguig": [
      "Bagumbayan", "Bambang", "Calzada", "Central Bicutan", "Central Signal Village",
      "Fort Bonifacio", "Hagonoy", "Ibayo-Tipas", "Katuparan", "Ligid-Tipas",
      "Lower Bicutan", "Maharlika Village", "Napindan", "New Lower Bicutan", "North Daang Hari",
      "North Signal Village", "Palingon", "Pinagsama", "San Miguel", "Santa Ana",
      "South Daang Hari", "South Signal Village", "Tanyag", "Tuktukan", "Upper Bicutan",
      "Ususan", "Wawa", "Western Bicutan"
    ]
  },
  "CALABARZON": {
    "Antipolo": [
      "Bagong Nayon", "Beverly Hills", "Calawis", "Cupang", "Dalig",
      "Dela Paz", "Inarawan", "Mambugan", "Mayamot", "Muntindilaw",
      "San Isidro", "San Jose", "San Juan", "San Luis", "San Roque", "Santa Cruz"
    ],
    "Taytay": [
      "Dolores", "Muzon", "San Isidro", "San Juan", "Santa Ana"
    ]
  }
};

export const PASIG_BARANGAY_CENTROIDS: Record<string, [number, number]> = {
  "bagong ilog": [14.565254, 121.069000],
  "bagong katipunan": [14.558597, 121.075193],
  "bambang": [14.554780, 121.078653],
  "buting": [14.554785, 121.067741],
  "caniogan": [14.571951, 121.080520],
  "dela paz": [14.613554, 121.095793],
  "kalawaan": [14.551481, 121.086725],
  "kapasigan": [14.564499, 121.074174],
  "kapitolyo": [14.571258, 121.059267],
  "malinao": [14.557603, 121.078579],
  "manggahan": [14.603896, 121.099242],
  "maybunga": [14.573879, 121.098035],
  "oranbo": [14.573583, 121.064245],
  "palatiw": [14.563063, 121.084919],
  "pinagbuhatan": [14.557297, 121.090992],
  "pineda": [14.566581, 121.059579],
  "rosario": [14.590928, 121.087306],
  "sagad": [14.566274, 121.079462],
  "san antonio": [14.583057, 121.061801],
  "san joaquin": [14.552226, 121.075712],
  "san jose": [14.561303, 121.073645],
  "san miguel": [14.565805, 121.085476],
  "san nicolas": [14.560669, 121.080379],
  "santa cruz": [14.563571, 121.078921],
  "santa lucia": [14.584264, 121.101303],
  "santa rosa": [14.557324, 121.070366],
  "santo tomas": [14.562841, 121.081683],
  "santolan": [14.621693, 121.086314],
  "sumilang": [14.556648, 121.073891],
  "ugong": [14.584131, 121.073246],
};

export function resolveProfileCoordinates(
  barangay?: string | null,
  _city?: string | null
): { lat: number; lng: number } | null {
  if (!barangay) return null;
  const cleanBgy = barangay.toLowerCase().replace(/^(barangay|brgy\.?)\s+/i, '').trim();
  if (PASIG_BARANGAY_CENTROIDS[cleanBgy]) {
    const [lat, lng] = PASIG_BARANGAY_CENTROIDS[cleanBgy];
    return { lat, lng };
  }
  return null;
}
