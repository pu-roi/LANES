param(
    [string]$Region = "asia-east1",
    [string]$BackendService = "lanes-api",
    [string]$ValhallaService = "lanes-valhalla",
    [string]$TileVersion = "philippines-2026-07-13"
)

$ErrorActionPreference = "Stop"
$projectId = (gcloud config get-value project).Trim()
if (!$projectId) { throw "Select a Google Cloud project with 'gcloud config set project PROJECT_ID'." }

$bucket = "$projectId-lanes-valhalla-tiles"
$tileSource = "$PSScriptRoot\..\..\data\valhalla\custom_files"
foreach ($file in @("valhalla_tiles.tar", "valhalla.json", "file_hashes.txt")) {
    if (!(Test-Path "$tileSource\$file")) { throw "Missing routing artifact: $tileSource\$file" }
}

gcloud storage buckets describe "gs://$bucket" 2>$null
if ($LASTEXITCODE -ne 0) {
    gcloud storage buckets create "gs://$bucket" --location=$Region --uniform-bucket-level-access
}

$artifactPath = "gs://$bucket/valhalla/$TileVersion"
gcloud storage ls "$artifactPath/valhalla_tiles.tar" 2>$null
if ($LASTEXITCODE -eq 0) {
    throw "Tile version '$TileVersion' already exists. Choose a new immutable TileVersion instead of overwriting it."
}
gcloud storage cp "$tileSource\valhalla_tiles.tar" "$artifactPath/valhalla_tiles.tar"
gcloud storage cp "$tileSource\valhalla.json" "$artifactPath/valhalla.json"
gcloud storage cp "$tileSource\file_hashes.txt" "$artifactPath/file_hashes.txt"

gcloud artifacts repositories describe lanes --location=$Region 2>$null
if ($LASTEXITCODE -ne 0) {
    gcloud artifacts repositories create lanes --repository-format=docker --location=$Region
}

gcloud builds submit --config=infrastructure/valhalla/cloudbuild.yaml --substitutions="_ARTIFACT_BUCKET=$bucket,_TILE_VERSION=$TileVersion" .
$image = "$Region-docker.pkg.dev/$projectId/lanes/lanes-valhalla:$TileVersion"
gcloud run deploy $ValhallaService --image=$image --region=$Region --no-allow-unauthenticated --cpu=2 --memory=4Gi --concurrency=8 --timeout=60 --min-instances=0

$backendServiceAccount = (gcloud run services describe $BackendService --region=$Region --format="value(spec.template.spec.serviceAccountName)").Trim()
if (!$backendServiceAccount) { throw "Set an explicit runtime service account on $BackendService before granting Valhalla access." }
gcloud run services add-iam-policy-binding $ValhallaService --region=$Region --member="serviceAccount:$backendServiceAccount" --role="roles/run.invoker"

$valhallaUrl = (gcloud run services describe $ValhallaService --region=$Region --format="value(status.url)").Trim()
gcloud run services update $BackendService --region=$Region --update-env-vars="ENVIRONMENT=production,VALHALLA_URL=$valhallaUrl,VALHALLA_AUDIENCE=$valhallaUrl"

Write-Host "Private Valhalla deployment complete: $valhallaUrl" -ForegroundColor Green
