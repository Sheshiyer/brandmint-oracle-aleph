# Brandmint Design Memory Worker

Cloudflare Worker service for visual reference retrieval. It indexes images from `/Volumes/madara/2026/twc-vault/03-Resources/Design`, polls NVIDIA NIM for embedding models first, stores metadata and vectors in KV, and returns ranked image references for Brandmint generation flows.

## Architecture

- Worker secret `NVIDIA_API_KEY`: NVIDIA NIM API key.
- Optional Worker secret `ADMIN_TOKEN`: protects `/models/poll` and `/ingest`.
- KV binding `DESIGN_KV`: model cache, asset metadata, vector records, asset list.
- Local scanner `scripts/scan_design_images.py`: builds JSONL manifest from local design images.

The NVIDIA key is never stored in KV. KV stores only model metadata, image metadata, and embeddings.

## Setup

```bash
cd services/design-memory-worker
npm install
wrangler kv namespace create DESIGN_KV
wrangler kv namespace create DESIGN_KV --preview
wrangler secret put NVIDIA_API_KEY
wrangler secret put ADMIN_TOKEN
```

Copy the created namespace IDs into `wrangler.toml`.

## Scan Local Design Images

```bash
python3 scripts/scan_design_images.py \
  --root /Volumes/madara/2026/twc-vault/03-Resources/Design \
  --out data/design-assets.jsonl
```

Use `--include-data-uri` only for small batches if a future NVIDIA visual model requires inline image input. The default manifest uses metadata and captions so it stays lightweight.

This repository currently scanned 135 records into `data/design-assets.jsonl`.

## Poll NVIDIA Models

```bash
curl -X POST https://brandmint-design-memory.<subdomain>.workers.dev/models/poll \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

The Worker calls `GET https://integrate.api.nvidia.com/v1/models`, ranks embedding candidates, and caches the selected model in KV. It prefers multimodal or image-capable embedding models, then falls back to known NVIDIA text embedding families.

## Ingest Records

```bash
ADMIN_TOKEN="paste-your-admin-token" python3 scripts/ingest_manifest.py \
  --worker-url https://brandmint-design-memory.<subdomain>.workers.dev \
  --manifest data/design-assets.jsonl \
  --batch-size 20
```

## Search References

```bash
curl -X POST https://brandmint-design-memory.<subdomain>.workers.dev/search \
  -H "Content-Type: application/json" \
  -d '{"query":"cinematic launch hero with premium wellness texture","aspect":"16:9","limit":5}'
```

Returned asset paths can be passed into the Brandmint `gpt-image2` provider as reference images.
