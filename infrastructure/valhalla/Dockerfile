FROM ghcr.io/gis-ops/docker-valhalla/valhalla:latest

# Cloud Build downloads these ignored, versioned artifacts before building.
COPY artifacts/ /custom_files/
COPY --chmod=755 start.sh /usr/local/bin/lanes-valhalla-start

ENV use_tiles_ignore_pbf=True \
    build_tar=False \
    serve_tiles=True \
    update_existing_config=False

ENTRYPOINT ["/usr/local/bin/lanes-valhalla-start"]
