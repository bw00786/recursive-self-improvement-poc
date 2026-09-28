FROM python:3.12-slim

# Minimal runtime for candidate evaluation. The candidate workspace and the
# immutable benchmark are mounted read-only at runtime (-v ...:/work:ro).
RUN pip install --no-cache-dir pyyaml httpx

WORKDIR /work
ENTRYPOINT ["python"]
