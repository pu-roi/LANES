# Same application/reader files as the pinned historical worker.
ARG HISTORY_IMAGE=lanes-news-history:part2a-batches-v1
FROM ${HISTORY_IMAGE}
USER root
# Existing API modules create these operational directories during import.
# Keep source, model assets and private seed manifests owned by root.
RUN mkdir -p /app/backups /app/exports /app/data \
    && ln -s /app/data/weather-cache.sqlite /app/.cache.sqlite \
    && chown 65532:65532 /app/backups /app/exports /app/data
USER 65532:65532
ENV SQLITE_TMPDIR=/tmp
ENTRYPOINT ["python", "-B", "-m", "uvicorn", "app.main:app"]
CMD ["--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "*"]
