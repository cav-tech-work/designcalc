# DesignCalc — Architecture

## Shape

```
┌─────────────────────────────┐        POST /api/generate         ┌──────────────────────────┐
│  Next.js frontend (Vercel)  │  ── { width_ft, depth_ft, units } ──▶│  Python serverless func   │
│                             │                                    │  api/generate.py          │
│  app/page.tsx               │                                    │    │                      │
│   ├─ VenueForm              │                                    │    ▼                      │
│   ├─ PlanPreview  (SVG)     │◀── { design, meta, dbpr_base64 } ──│  api/_engine/engine.py    │
│   ├─ SubsystemCards         │                                    │    generate() → .dbpr     │
│   └─ PartsList (+CSV)       │                                    │  api/_engine/summary.py   │
│                             │                                    │    read .dbpr → summary   │
└─────────────────────────────┘                                    └──────────────────────────┘
```

One Vercel project. The frontend is static/SSR Next.js; the engine is a Python function in
`api/`. They communicate over a single JSON endpoint (the contract in `PRD_DesignCalc.md §9`).

## Request lifecycle

1. User submits width + depth (+ units) in `app/page.tsx`.
2. `fetch("/api/generate", …)` posts JSON.
3. `api/generate.py`:
   - validates ranges (30–800 ft wide, 30–900 ft deep),
   - converts metres→feet if needed,
   - calls `engine.generate(depth_ft, width_ft, /tmp/…​.dbpr)` — the **proven** generator,
   - calls `summary.summarize(path)` to read the file back into a UI-friendly summary,
   - base64-encodes the `.dbpr`,
   - returns `{ design, meta, dbpr_base64, filename }`,
   - deletes the temp file (stateless).
4. Frontend renders the plan, cards, notes and parts, and offers the `.dbpr` + CSV downloads.

## Why the engine is reused as-is (not ported)

The generator encodes a real designer's flat-ground house style and, critically, the
`.dbpr`/SQLite subtleties that make a file open cleanly in ArrayCalc (skeleton cloning,
integrity, symmetric L/R pairing, ArrayProcessing slots, amplifier patching, never touching
`ProjectInformation`). Re-deriving all of that in TypeScript would be weeks of high-risk
work. Treating it as a black box behind a stable API is the fastest correct path and gives a
future dev team a clean seam.

## Key design choices

- **File is the source of truth.** The preview, cards and parts list are all derived by
  reading the generated `.dbpr` (`summary.py`), so the UI can never disagree with the
  downloadable file.
- **base64-in-JSON delivery.** The `.dbpr` rides back in the JSON response — no server-side
  temp handoff, no second request, fully stateless. (For very large files later, switch to a
  token + `GET /api/download` without changing the frontend contract much.)
- **No external Python deps.** Only the standard library (`sqlite3`, `base64`, `json`,
  `http.server`), so cold starts are fast and the function is trivial to build.
- **Coordinates.** Engine works in metres: `OriginX` = depth from stage, `OriginY` = lateral
  (+L / −R). The SVG preview maps depth→vertical (stage at top) and lateral→horizontal.

## Extension points (roadmap)

- **Advanced mode:** add fields to the form and pass more parameters into `engine.generate`
  (the engine already parameterises quantities; expose the knobs). Contract gains optional
  fields; response shape unchanged.
- **Upload & revamp:** new endpoint `POST /api/revamp` that accepts a `.dbpr`, extracts the
  venue via a reader, and calls the engine. Reuses `summary.py`.
- **Preview v2:** a side-section component consuming the same `design` object (`trim`,
  `aim_deg`, `lowest_edge_ft` are already present).
```
