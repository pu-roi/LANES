# Metro Manila NOAH analytical bundle

Attribution: **Project NOAH and its contributors**. This derived database is
distributed under **Open Database License 1.0 (ODbL-1.0)**, with the attribution
and share-alike terms of the [original Project NOAH license](https://huggingface.co/datasets/bettergovph/project-noah-hazard-maps/resolve/main/NOAH_License.pdf)
and [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/).

Source: the three Metro Manila 5-, 25-, and 100-year archives from the
[Project NOAH hazard maps dataset](https://huggingface.co/datasets/bettergovph/project-noah-hazard-maps).
`manifest.json` records each original archive SHA-256 and every derived tile
checksum, attribution, scenario, bounded extent, and license. No original ZIPs
or national dataset are included. These modeled hazards do not establish
current flooding or measured flood depth/width.

Release identity (manifest SHA-256):
`cceb8c93d5441f14aad48808319a3d4cf3a87918ea8089dcb5efbf86c49940ce`.
The bundle contains 897 gzip tiles totaling 89,708,051 compressed bytes.
Tile geometry and manifest bytes are unchanged from the local analyzed catalog.

The API and worker use this same immutable Git/container snapshot. Docker copies
it to `/data/noah-placement`; `LANES_NEWS_NOAH_DIR` may select another explicitly
provisioned catalog. The local default is this bundled directory as well.

From `backend`, verify all spatial bundle checksums and parent coverage without
provider requests or database access:

```powershell
.\venv\Scripts\python.exe -m scripts.verify_news_runtime_assets
```

For a reviewed refresh, build a **new** catalog with
`scripts.build_noah_placement_catalog`, then copy it to a new snapshot directory
with `scripts.package_news_noah_assets`. Review its source identities, licensing,
geometry, checksums, coverage and tests before switching the release snapshot.
