FROM ghcr.io/gis-ops/docker-valhalla/valhalla:latest

# Cloud Build downloads these ignored, versioned artifacts before building.
COPY artifacts/ /custom_files/
COPY start.sh /usr/local/bin/lanes-valhalla-start
RUN chmod +x /usr/local/bin/lanes-valhalla-start && mkdir -p /custom_files/valhalla_tiles

ENV use_tiles_ignore_pbf=True \
    build_tar=False \
    serve_tiles=True \
    update_existing_config=False

ENTRYPOINT ["/usr/local/bin/lanes-valhalla-start"]
