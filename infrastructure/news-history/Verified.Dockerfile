# Authenticated existing Linux dependency base; no package/model changes.
ARG QUALIFIED_BASE=lanes-ner-qualified-base:phase-b
FROM ${QUALIFIED_BASE} AS qualified
USER root
RUN rm -rf /app /assets /seed /data /input /output /root/.cache
FROM scratch
COPY --from=qualified / /
WORKDIR /app
COPY app/ /app/app/
COPY scripts/ /app/scripts/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/alembic.ini
COPY runtime_data/ /data/
COPY runtime_data/ /app/runtime_data/
COPY assets/ /assets/
COPY release/ /release/
RUN mkdir -p /app/backups /app/exports /app/data \
    && ln -s /app/data/weather-cache.sqlite /app/.cache.sqlite \
    && chown 65532:65532 /app/backups /app/exports /app/data
ENV PATH=/usr/local/bin:/usr/bin:/bin LANG=C.UTF-8 PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 CUDA_VISIBLE_DEVICES="" \
    LANES_HISTORY_RESOURCE_PROFILE=cloud-run-v1 SQLITE_TMPDIR=/tmp
USER 65532:65532
ENTRYPOINT ["python","-B","-m","scripts.news_verified_entrypoint"]
CMD ["preflight"]
