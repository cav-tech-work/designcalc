# DesignCalc

Flat-ground **d&b audiotechnik** system designer. Enter a rectangular open-air venue's
width and depth and DesignCalc lays out a complete house-style system — mains, subs, fills
and delays — as a top-down plan and a valid **ArrayCalc `.dbpr`** project you can open and
refine.

> MVP scope: **Simple mode** (venue dimensions in → design out). Advanced mode and
> Upload/revamp are on the roadmap — see `PRD_DesignCalc.md`.

---

## Stack

- **Frontend:** Next.js 14 (App Router, TypeScript, React 18) — no CSS framework, hand-rolled
  d&b-branded styles in `app/globals.css`.
- **Engine API:** Python serverless function (`api/generate.py`) wrapping the existing,
  proven flat-ground generator in `api/_engine/`. Standard library only — no pip deps.
- **Deploy target:** Vercel (single project; Next.js frontend + Python function together).
- **Stateless:** no database, no auth. Nothing is stored.

## Local development

```bash
npm install
npm run dev          # Next.js on http://localhost:3000
```

The `/api/generate` Python function runs on Vercel (and `vercel dev`). To run the API
locally the easy way:

```bash
npm i -g vercel
vercel dev           # serves the frontend AND the Python function together
```

To exercise the engine directly (no web layer):

```bash
cd api/_engine
python3 engine.py 450 220 out.dbpr     # depth_ft width_ft -> out.dbpr
```

## Deploy to Vercel

1. Push this repo to GitHub.
2. In Vercel: **New Project → import the repo**. Framework preset auto-detects Next.js.
3. No environment variables needed for the MVP.
4. Deploy. The Python function under `api/` is built automatically (`@vercel/python`).

`vercel.json` allocates the function 1 GB / 30 s, which is ample for the engine.

## Project layout

```
DesignCalc/
├── app/                  # Next.js frontend (App Router)
│   ├── page.tsx          # form + results orchestration (client)
│   ├── layout.tsx
│   ├── globals.css       # d&b brand tokens + styles
│   └── components/       # PlanPreview (SVG), SubsystemCards, PartsList
├── api/
│   ├── generate.py       # Vercel serverless handler (POST /api/generate)
│   ├── requirements.txt  # (empty — stdlib only)
│   └── _engine/          # the proven generator, treated as a black box
│       ├── engine.py         # generate(depth_ft, width_ft, out_path)
│       ├── flatground_core.py
│       ├── extensions.py
│       ├── writer.py
│       ├── summary.py        # reads a .dbpr -> design summary for the UI
│       └── NewProject_Skeleton.dbpr   # blank ArrayCalc project (cloned per request)
├── lib/                  # shared TS types + colour palette
├── PRD_DesignCalc.md     # product requirements + decision log
├── ARCHITECTURE.md       # how it fits together
├── HANDOFF.md            # dev-team handoff notes
└── vercel.json
```

## The one rule that must never break

Every generated `.dbpr` must open in ArrayCalc with **no validation warning and no
password prompt**. The engine guarantees this by cloning a genuine blank ArrayCalc project
and never touching `ProjectInformation`. **Do not** post-process or rewrite the `.dbpr`
after the engine produces it.

## Roadmap

See `PRD_DesignCalc.md §12`. Next up: Advanced mode (expose engine parameters), then
Upload & revamp (read a `.dbpr`'s venue and redesign).
