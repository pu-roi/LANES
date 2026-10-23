# Build only from the locally authenticated qualification base, never the API build.
ARG QUALIFIED_BASE=lanes-ner-qualified-base:phase-b
FROM ${QUALIFIED_BASE} AS qualified

# The base supplies the frozen Python/native dependencies. Remove its application
# filesystem; this job has no API, database configuration or scheduled entrypoint.
USER root
RUN rm -rf /app /data /assets /input /output /root/.cache

# Export the cleaned filesystem into a new image so inherited application/test
# files also stay out of its lower layers. Keep the qualified native libraries.
FROM scratch
COPY --from=qualified / /
WORKDIR /app
COPY app/ /app/app/
COPY scripts/ /app/scripts/
COPY assets/ /assets/
COPY input/ /input/
ENV PATH=/usr/local/bin:/usr/bin:/bin LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    CUDA_VISIBLE_DEVICES="" LANES_NER_CHECK_PROFILE=isolated
USER 65532:65532
ENTRYPOINT ["python", "-I", "-B", "/app/scripts/news_ner_cloud_entrypoint.py"]
CMD []
