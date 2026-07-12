# CLAUDE.md — DesignCalc

Project memory for Claude Code (and any AI assistant) working in this repo. Read this first.

## What this is

DesignCalc is a web app that turns a flat, rectangular open-air venue's dimensions into a
house-style **d&b audiotechnik** sound-system design, shown as a top-down plan and
downloadable as a valid **ArrayCalc `.dbpr`** project, with a parts list.

- **Live:** https://designcalc-roan.vercel.app
- **Repo:** https://github.com/cav-tech-work/designcalc (private; org `cav-tech-work`)
- **Owner:** Joyjeet Panday. Claude acts as PM + builder.
- Full product spec: `PRD_DesignCalc.md`. Architecture: `ARCHITECTURE.md`. Handoff: `HANDOFF.md`.

## Stack

- Next.js 14 (App Router, TypeScript, React 18) frontend — hand-rolled d&b-branded CSS in
  `app/globals.css`, no CSS framework.
- Python serverless function `api/generate.py` wrapping the design engine in `api/_engine/`
  (standard library only, no pip deps).
- Vercel deploy (one project: frontend + Python function). Stateless — no DB, no auth.

## HARD CONSTRAINTS — never violate

1. **Never modify, re-save, or post-process a generated `.dbpr`** after the engine writes it.
   The API must only READ it. Altering it breaks ArrayCalc's integrity hash → password prompt.
2. **Do not delete or regenerate** `api/_engine/NewProject_Skeleton.dbpr` — it's the blank
   ArrayCalc project the engine clones. The app breaks without it.
3. **Do not change the design-engine logic** in `api/_engine/` (`flatground_core.py`,
   `extensions.py`, `writer.py`, `engine.py`, `summary.py`) unless the task is explicitly
   an engine change. It encodes a real designer's house style and hard-won `.dbpr` correctness.
4. **Keep it stateless** — no database, no auth, no stored files.
5. Keep the API contract in sync: `lib/types.ts` ↔ `api/generate.py` response shape.

## The one acceptance test

Every generated `.dbpr` must open in ArrayCalc with **no validation warning and no password
prompt**. If you touch anything near generation, re-verify this.

## Dev workflow (this is the point of using Claude Code here)

- **Local dev:** `pnpm install` then `vercel dev` (NOT plain `next dev` — the Python API only
  runs under Vercel's dev server). This machine uses pnpm/node; npm may not be on PATH.
- **Build check:** `pnpm build` (or `npx next build`). Must compile + type-check clean.
- **Ship a change:**
  ```bash
  git add -A
  git commit -m "..."
  git push origin main    # with GitHub↔Vercel linked, this auto-deploys
  ```
- If a previous session left git lock files (from a sandboxed environment), clear them first:
  `rm -f .git/HEAD.lock .git/objects/maintenance.lock .git/objects/*/tmp_obj_*`

## Layout

```
app/            Next.js frontend (page.tsx = form + results; components/ = PlanPreview, SubsystemCards, PartsList)
api/generate.py Vercel serverless handler (POST /api/generate)
api/_engine/    the design engine (black box — see constraint #3) + NewProject_Skeleton.dbpr
lib/            shared TS types + colour palette
preview/        static HTML snapshot of the results screen (for quick visual checks)
```

## Preview / plan-drawing note

The top-down plan uses a **fixed downstage band** for near-stage systems (mains, subs, fills,
out fills — all within ~2 m of the stage, so not to depth-scale) and a **to-scale field**
below for delay towers. This avoids the overlap you'd get drawing everything at true depth.
The same logic lives in `app/components/PlanPreview.tsx` and `preview/designcalc_preview.html` —
keep them in sync. Known polish item: label crowding on very narrow venues (< ~60 ft wide).

## Roadmap (not built yet)

1. ~~**Advanced mode**~~ — **shipped.** Hybrid overrides (positional/quantity hard + clamped;
   frame/splay/trim guided). See `ADVANCED_MODE_SPEC.md`.
2. **Upload & revamp** — drag in a `.dbpr`, read its venue, redesign/improve.
3. Preview v2 (side-section), accounts/saved designs, then beyond flat ground.

## Decision log

See `PRD_DesignCalc.md §14` for approved decisions (primary user = rental/production shop;
Simple mode first; reuse Python engine; stateless; name = DesignCalc; etc.).
