# Extraction runtime references

Docker copies these reviewed reference snapshots to `/data`, where the existing
location and Pasig history services resolve their data paths inside `/app`.
These files are required for container extraction to match development behavior.

- `philippines_psgc_reference.csv`: 43,778 official administrative records.
- `pasig_barangay_reference.csv`: 30 Pasig barangays.
- `flooded_areas_pasig_clean.csv`: 726 cleaned historical records; these are
  contextual records, not independently verified flood events or live evidence.
- `osm/` and `barangay/`: checksummed road and qualified community-boundary catalogs.
- `noah-placement/`: the bounded Metro Manila analytical bundle; see its README
  for ODbL attribution, source identities and reproducible verification. Docker
  checks the whole spatial bundle before producing a release image.

When refreshing the corresponding repository `data/` files, review the changes,
copy the approved snapshots here, run the news extraction tests, and rebuild.
From the repository root, build the backend with
`docker build -f backend/Dockerfile backend`.
Do not include credentials, full hazard archives, or unrelated datasets here.
