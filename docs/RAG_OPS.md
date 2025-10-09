## RAG Operations Guide

This guide describes how to operate and maintain Jarvis Core's RAG subsystem in production.

### Backends and persistence

Supported backends (via `configs/vectorstore.yaml`):
- `memory`: in-memory index (non-persistent)
- `persistent`: JSONL-based persistence with file locks and backups
- `faiss`: FAISS index with separate `index.faiss` and `texts.jsonl`
- `annoy`: Annoy index with `index.ann` and `texts.jsonl`

Example `configs/vectorstore.yaml`:
```yaml
backend: faiss
persist_dir: /workspace/data/vectorstore
```

### Re-embedding

Enable automated re-embed on ingest via `configs/features.yaml`:
```yaml
features:
  reembed_on_ingest: true
```

Manual re-embed via API:
- Endpoint: `POST /rag/reembed`
- Auth: `Authorization: Bearer $API_TOKEN`
- Body:
```json
{
  "persist_dir": "/workspace/data/vectorstore",
  "backend": "faiss"
}
```

The re-embed pipeline rebuilds vectors using the current embedding adapter, reloads the selected backend, and saves artifacts back to `persist_dir`.

### Provenance and citations

Each chunk carries provenance metadata:
- `doc_id`: stable hash of the source path
- `page`: page number (if available)
- `chunk_index`: 0-based chunk order
- `start`, `end`: character offsets within the source text

Citations include the top snippet and the best available provenance anchors.

### Backups and file locks

The persistent JSONL backend writes timestamped backup files and uses a simple lock file to avoid concurrent writes. For FAISS/Annoy, the index and texts file are written atomically per save call.

### Operational tips
- Keep `persist_dir` on a durable volume.
- Schedule periodic re-embedding when upgrading embedding models.
- Use the `/rag/reembed` endpoint for on-demand maintenance.
- Monitor API logs for re-embed completion and errors.
