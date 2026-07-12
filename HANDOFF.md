# DesignCalc — Handoff Notes (for the dev team / Cursor)

This repo is intentionally small and deployable as-is. Read this, then `README.md` and
`ARCHITECTURE.md`.

## What's done (MVP, Simple mode)

- ✅ Next.js frontend: venue form, top-down SVG plan, subsystem cards, parts list + CSV,
  `.dbpr` download, d&b-branded styling, loading/empty/error states.
- ✅ Python serverless API (`api/generate.py`) wrapping the proven engine, with input
  validation and stateless base64 delivery.
- ✅ Engine bundled in `api/_engine/` (unchanged behaviour) + a `.dbpr`→summary reader.
- ✅ `vercel.json`, `.gitignore`, docs. `next build` compiles and type-checks clean.

## What's NOT done (by design — roadmap)

- Advanced mode, Upload/revamp mode.
- Accounts, saved designs, share links.
- Pricing/quotes.
- Side-section / 3D preview.
- Automated tests (see below — add these first).

## First things a dev should do

1. **Run it.** `npm install && vercel dev`, generate a 450×220 design, download the `.dbpr`,
   open in ArrayCalc → confirm no warning/password. This is the acceptance test.
2. **Add tests.**
   - Python: unit-test `engine.generate` + `summary.summarize` on a few venue sizes
     (assert integrity `ok`, expected subsystem counts, box totals).
   - Frontend: a component test for `PlanPreview` scaling and an e2e (Playwright) for the
     generate→download flow.
3. **CI.** GitHub Actions: `next build` + `python -m pytest` on PRs.
4. **Error surface.** The API returns a `trace` on 500 for debugging — gate that behind a
   non-production flag before real launch.

## Guardrails / gotchas

- **Never mutate the `.dbpr` after the engine writes it** (breaks the ArrayCalc integrity
  hash → password prompt). The API only reads it.
- The blank skeleton `api/_engine/NewProject_Skeleton.dbpr` is a **required asset** — it's the
  genuine ArrayCalc project that gets cloned per request. Don't strip or regenerate it by hand.
- Input ranges live in `api/generate.py` (`MIN_FT`, `MAX_W_FT`, `MAX_D_FT`). Adjust to match
  what the engine handles safely; keep the frontend hints in sync.
- The engine writes to `/tmp` (the only writable path on Vercel). Keep it that way.

## The stable contract

`POST /api/generate` ↔ the `GenerateResponse` type in `lib/types.ts`. Frontend and engine
can evolve independently as long as this holds. If you change the response shape, update
`lib/types.ts` and the three render components together.

## Ownership map

| Area | Files |
|------|-------|
| Product spec + decisions | `PRD_DesignCalc.md` |
| Frontend UI | `app/`, `lib/` |
| API boundary | `api/generate.py`, `lib/types.ts` |
| Design engine (house style) | `api/_engine/*` (see the `db-system-design` skill refs) |
| Deploy | `vercel.json`, Vercel project settings |
