FROM python:3.12-slim

# docker CLI (sandbox launches sibling containers) + git (candidate branches)
RUN apt-get update && apt-get install -y --no-install-recommends \
    docker.io git && rm -rf /var/lib/apt/lists/*

WORKDIR /repo
COPY backend/pyproject.toml backend/pyproject.toml
RUN pip install --no-cache-dir -e "backend[dev]"

COPY . /repo
ENV PYTHONPATH=/repo
EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
