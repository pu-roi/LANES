# Private Valhalla deployment

Run `./infrastructure/valhalla/deploy.ps1` from an authenticated Google Cloud SDK shell after selecting `lanes-project-508809`.

The script uploads the ignored Philippines tile archive to a private regional bucket, builds an immutable image through Cloud Build, deploys private `lanes-valhalla`, grants only the FastAPI runtime service account `roles/run.invoker`, and configures `lanes-api` to call it with an ID token.

Before running it, assign an explicit runtime service account to `lanes-api`; the script intentionally refuses to grant access to an implicit default identity. The Cloud Build service account also needs read access to the tile bucket and permission to push to the `lanes` Artifact Registry repository. Choose a new `-TileVersion` for every tile/config update—the script will refuse to overwrite an existing artifact version.

The uploaded `valhalla.json` must set `service_limits.max_alternates` to at least `3`; LANES requests three alternates to produce up to four route cards.

After deployment, verify the following from an authenticated Cloud SDK shell:

```powershell
$valhallaUrl = (gcloud run services describe lanes-valhalla --region=asia-east1 --format="value(status.url)").Trim()

# Backend can obtain a route through the private service.
Invoke-RestMethod -Method Post "https://lanes-api-557679867071.asia-east1.run.app/api/v1/reports/route" -ContentType "application/json" -Body '{"start":[121.0244,14.5547],"end":[121.039,14.58]}'

# A public caller cannot invoke the private Valhalla service.
Invoke-WebRequest "$valhallaUrl/route" -Method Post -ContentType "application/json" -Body '{"locations":[]}'
```

The first response should report `engine_used: valhalla` and `fallback_used: false`. The second request must be denied (401/403). To exercise the ORS fallback, temporarily remove the `roles/run.invoker` binding for the backend runtime account, make one route request, confirm `engine_used: ors` and `fallback_used: true`, then restore the binding immediately.
