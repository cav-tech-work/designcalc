# DesignCalc — Product Requirements Document (MVP)

**Owner:** Joyjeet Panday
**PM / build:** Claude
**Status:** Draft v1 — for review
**Last updated:** 2026-07-13

---

## 1. One-line summary

DesignCalc is a web app that turns a flat, rectangular open-air venue's dimensions
into a complete, house-style d&b sound system design — shown as a top-down plan in the
browser and downloadable as a valid ArrayCalc `.dbpr` project file, with a parts list.

## 2. Problem & why now

Designing a festival/open-ground PA in ArrayCalc from a blank project is slow and
expert-only: you place every array, set splay, trim, delays, and patch by hand. Rental
and production shops repeat this work for every gig, largely re-deriving the same
house-style decisions each time.

We already have a proven engine that encodes one experienced designer's flat-ground house
style and writes valid `.dbpr` files (correct SQLite skeleton cloning, integrity, pairing,
patching). DesignCalc puts that engine behind a simple web form so a shop can go from
"how big is the field?" to a ready-to-open ArrayCalc project in seconds, then refine in
ArrayCalc as normal.

## 3. Target user (MVP)

**Primary persona — the rental / production shop system tech.**
Specs repeatable open-ground rigs for festivals and events. Comfortable in ArrayCalc but
wants a fast, credible starting design rather than a blank canvas. Values: speed, sensible
defaults, a design they can trust and then tweak, and a parts count for pulling gear.

Not optimized for in MVP (still valid future users): pre-sales reps, students, arena/
multi-plane designers.

## 4. Product vision (north star — NOT all in MVP)

Three ways to get a design, all sharing one engine:

1. **Simple mode** — width + depth → full auto design. *(MVP)*
2. **Advanced mode** — width + depth **plus** user-controlled parameters (mains L/R spread,
   delay distances, box counts per array, input source per array, etc.). *(Roadmap — fast-follow)*
3. **Upload & revamp** — drag in an existing `.dbpr`; DesignCalc reads the venue and either
   redesigns from scratch or improves the existing design. *(Roadmap — phase 2)*

Scope discipline: all three stay on the roadmap; only Simple mode ships in v1.

## 5. MVP scope (what ships in v1)

### In scope
- **Simple mode only.** Inputs: venue **width** and **depth** (feet), flat rectangular
  ground. Optional: a couple of low-risk toggles (e.g. units ft/m) — see §7.
- **Design engine:** the existing Python flat-ground generator, unchanged in behavior,
  exposed as an API. Quantities scale with venue size; design principles are invariant.
- **Deliverables per run:**
  1. **Top-down 2D plan preview** (SVG) — venue rectangle, stage edge, mains L/R, sub
     array, front fills, out fills, delay rings, with labels. d&b-branded styling.
  2. **Subsystem cards** — one card per array/system: box type + count, position,
     aim/trim, delay time, input source label.
  3. **`.dbpr` download** — the valid ArrayCalc project.
  4. **Parts list** — bill of materials: boxes by type, amplifiers, flying frames,
     counts. On-screen + CSV download.
- **Stateless.** No login, no database, nothing stored server-side beyond the request.
- **d&b brand-aligned UI.**

### Out of scope (explicit non-goals for v1)
- Advanced mode and Upload/revamp mode.
- Accounts, saved designs, share links, history.
- Pricing / quotes (removed from scope).
- Side-section / elevation view and 3D preview.
- Arenas, multi-plane venues, raked/curved audience areas, balconies.
- SPL simulation in-browser (ArrayCalc remains the acoustic authority).
- Editing the design in-browser (drag arrays, change counts) — that's Advanced mode.
- Non-d&b products; inventory constraints to a shop's owned stock.

## 6. Primary user flow (MVP)

1. Land on DesignCalc. Clear value line + a single primary form.
2. Enter venue **width** and **depth** (with a units toggle, default feet).
3. Click **Generate design.**
4. App calls the engine API; shows a loading state.
5. Results view renders: top-down plan (hero) + subsystem cards + parts list.
6. User clicks **Download .dbpr** (and optionally **Download parts CSV**).
7. User opens the `.dbpr` in ArrayCalc to verify/refine. Done.

Error/edge handling: invalid or out-of-range dimensions → inline validation with guidance;
engine error → friendly message + "try again"; no partial/blank downloads.

## 7. Functional requirements

### Inputs
- `width_ft` (number, required) — audience-area width. Range guardrails (e.g. 30–800 ft).
- `depth_ft` (number, required) — audience-area depth. Range guardrails (e.g. 30–900 ft).
- `units` (ft | m, default ft) — UI convenience; converted to the engine's expected units.
- (Everything else — box choice, splay, trims, delays, patch, sources — is auto-derived by
  the engine in Simple mode.)

### Outputs (API response, see §9)
- A design summary object (subsystems, positions, counts, aim, delay, source labels) that
  drives the preview and cards.
- The `.dbpr` binary (streamed as a download).
- A parts list object → rendered on screen and as CSV.

### Preview requirements
- Top-down, to-scale plan. Stage at one end, audience field as the rectangle.
- Render: mains L/R hangs, sub array (with stack count), front fills, out fills (if width
  triggers them), delay positions/rings. Distinct, legible labels.
- d&b styling: dark canvas, thin precise linework, single red accent for the arrays, high
  legibility. Responsive; usable on a laptop screen.

### Parts list requirements
- Group by category: line array boxes (by model), subs, point-source fills, amplifiers,
  flying frames. Show quantity per line and totals.
- CSV export mirrors the on-screen table.

## 8. Architecture (agreed)

- **Frontend:** Next.js (React, TypeScript) on Vercel. Single-page form → results.
- **Engine API:** the existing **Python** generator, wrapped as a **serverless function on
  the same Vercel project** (`/api/...`), reused as-is. No rewrite.
- **One repo, one deploy.** Python function bundles the blank `.dbpr` skeleton as a static
  asset; writes to `/tmp` at runtime; returns the file + JSON summary.
- **No database, no auth** in MVP (stateless).

Rationale: reuse the code we KNOW produces valid `.dbpr` files; give the future dev team a
clean frontend/API seam and a working engine rather than a risky port.

## 9. API contract (frontend ↔ engine)

This is the seam the dev team (and Cursor) build against. Finalized in the tech spec, but
the shape for MVP:

```
POST /api/generate
Request  (application/json):
  {
    "width_ft":  number,      // required
    "depth_ft":  number,      // required
    "units":     "ft" | "m"   // optional, default "ft"
  }

Response (application/json):
  {
    "design": {
      "venue": { "width_ft": number, "depth_ft": number },
      "subsystems": [
        {
          "id": string,              // "mains_L", "sub_array", "delay_1_R", ...
          "role": string,            // "Mains", "Sub Array", "Front Fills", ...
          "box_model": string,       // "KSL", "V-Series", "SL-SUB", "A-Series"
          "box_count": number,
          "position": { "x_m": number, "y_m": number },  // engine coords
          "aim_deg": number | null,
          "trim_m": number | null,
          "delay_ms": number | null,
          "source_label": string     // input source name
        }
      ],
      "parts": [
        { "category": string, "item": string, "qty": number }
      ]
    },
    "dbpr_token": string   // handle to download the generated file (see below)
  }

GET /api/download?token=...   → streams the .dbpr (application/octet-stream)
```

Alternative (simpler) MVP: `/api/generate` returns the `.dbpr` as base64 alongside the
JSON, avoiding a second request and any server-side temp handoff. Decide in tech spec;
both are stateless.

## 10. Non-functional requirements

- **Correctness first:** every generated `.dbpr` must open in ArrayCalc with no validation
  warning and no password prompt (the engine already guarantees this; API must not mutate
  the file after generation).
- **Latency:** target < ~5 s from Generate to results for typical venues.
- **Reliability:** invalid input never produces a broken file; clear errors instead.
- **Privacy:** nothing stored; inputs discarded after the response.
- **Accessibility:** keyboard-usable form, sufficient contrast (align with d&b's own
  accessibility stance).

## 11. Success criteria (how we know MVP works)

- A rental tech enters width + depth and downloads a `.dbpr` that opens clean in ArrayCalc.
- The preview matches what the `.dbpr` contains (same counts/positions).
- Parts list totals equal the boxes/amps in the file.
- Deploys to Vercel from the GitHub repo with no manual server ops.

## 12. Roadmap (post-MVP, in order)

1. **Advanced mode** — expose engine parameters (mains L/R spread, delay distances, box
   counts, per-array input sources). Same engine, richer form.
2. **Upload & revamp** — parse an uploaded `.dbpr`, extract the venue, redesign/improve.
3. **Preview v2** — side-section/elevation (trim, frame angle, vertical coverage).
4. **Accounts & saved designs** — login + DB for repeatable jobs.
5. **Parts/quote** — inventory + rate-card quoting (revisit if wanted).
6. Beyond flat ground: arenas, multi-plane, raked audience.

## 13. Handoff notes (for the dev team / Cursor)

- Repo is a single Next.js + Python-serverless project, deployable to Vercel out of the box.
- The Python engine is treated as a **black-box library** behind `/api/generate`; the
  design house-style lives there and is documented in the existing skill references.
- The **API contract (§9)** is the stable seam — frontend and engine can evolve
  independently as long as it holds.
- All product decisions and their rationale are captured in this PRD's decision log (§14).
- Accompanying docs to be produced with the repo: `README.md` (run/deploy), `ARCHITECTURE.md`,
  and a `HANDOFF.md` mapping PRD → code.

## 14. Decision log (approved)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Primary user | Rental / production shop |
| 2 | Core deliverable | Preview + .dbpr + parts (quote later removed) |
| 3 | Design model (vision) | Three modes: Simple, Advanced, Upload/revamp |
| 4 | MVP scope cut | Simple mode first |
| 5 | Engine strategy | Reuse Python engine as serverless API on Vercel |
| 6 | Accounts | Stateless, no login |
| 7 | Quote/pricing | Removed from scope |
| 8 | Preview fidelity | 2D top-down plan + subsystem cards, d&b-branded |
| 9 | Product name | DesignCalc |

## 15. Open questions (to resolve before/along build)

- Exact input range guardrails (min/max width & depth) — pull from what the engine handles
  safely.
- `.dbpr` delivery: base64-in-JSON vs. token + second GET (tech-spec decision).
- Parts list: include amplifier channel plan, or just device counts, in v1?
- Units default (ft assumed) and whether to show both.
