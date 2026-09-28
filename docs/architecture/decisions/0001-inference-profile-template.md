# ADR 0001 — Selected inference profile (template)

- Status: **OPEN — do not implement a model profile from this template**
- Date: `<date decided after access>`
- Requirement: current VPS OpenAI-compatible caller contract
- Host: `<actual GPU model/count/VRAM/driver/runtime/storage/network>`
- Model: `<exact repository and immutable revision; license checked>`
- Precision/quantization: `<measured choice and quality trade-off>`
- Serving engine/version/image: `<tested exact versions>`
- Context/input/output token cap: `<measurement preserving the full prompt and bounded sketch>`
- Max active requests: `<measured peak memory and latency>`
- API bind/secure transport/auth rotation: `<private HTTPS or encrypted tunnel>`
- p50/p95 latency: `<representative request from VPS>`
- Peak GPU memory: `<include weights, KV cache and engine overhead>`
- Calibration: `<approved example IDs/count, agreement and JSON-valid rate>`
- Rejected alternatives: `<evidence, not preference>`
- Rollback/replacement path: `<how VPS retries while preserving old provenance>`
- Approver: `<user / project owner>`

Do not approve a profile solely because parameter count or a vendor page says it can run on a nominal 48 GB GPU.
