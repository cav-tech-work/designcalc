# Cursor prompt — build DesignCalc Advanced mode

Open the DesignCalc repo in Cursor's Agent and paste the block below. Full detail lives in
`ADVANCED_MODE_SPEC.md`; this prompt drives the build in safe stages.

---

```
Build "Advanced mode" for DesignCalc per ADVANCED_MODE_SPEC.md (read it fully first, plus
CLAUDE.md). Work in STAGES and verify each before moving on. Do not start the UI until the
engine and API stages pass.

CONTEXT: Live Simple-mode app (Next.js + Python function in api/, engine in api/_engine/).
Advanced mode = user overrides of what the engine auto-derives. Philosophy is HYBRID:
positional/quantity params (mains spread, box counts, delay ring distances, sub/fill counts,
toggles, source labels) are HARD overrides but CLAMPED to safe ranges; acoustically-risky
params (frame angle, splay, trim) stay engine-derived. Every clamp must be reported as a
"notice". Simple mode must remain byte-for-byte unchanged.

STAGE 1 — ENGINE (api/_engine/), additive only; all new params default to current behaviour:
  - Add a clamp helper that records notices: clamp(value, lo, hi, field) -> (value, notice?).
  - flatground_core.design(system, throw, n_override=None): if n_override, use it as n and
    recompute splays=deep_j_splay(n), levels=mains_levels(n), arr_h, le, fa, z from it.
  - flatground_core.build_line(..., n_override=None): pass through to design().
  - flatground_core.build_core(api, depth_m, width_m, mains_variance_limit_m=None, adv=None):
      mains spread -> my = clamp(adv.mains.spread_ft/2 * FT, ~2 m, width_m/2 - 0.5) else mains_y(width_m);
      mains boxes -> n_override = clamp(adv.mains.boxes_per_side, 6, 24).
  - build_sub_array(api, width_m, adv=None): stacks clamp 3-14; spacing clamp 5-8 ft.
  - build_front_fills(api, width_m, mains_y_m, adv=None): enabled gate; count clamp even 4-12.
  - extensions.add_out_fills(api, width_m, mains_y_m, adv=None): enabled overrides the
    width>61 m rule; boxes_per_side via n_override (clamp 4-16).
  - extensions.add_delay_rings(..., adv=None): mode "manual" places one symmetric ring per
    entry at x = distance_ft*FT (clamp mains_reach..far_edge-~12 m, max 4), boxes via
    n_override; keep the system rule (ring1=KSL if >1 else V) and dly=(x-1.5)/343. mode
    "auto"/absent = unchanged.
  - engine.generate(depth_ft, width_ft, out_path, mains_variance_limit_ft=None, adv=None):
    thread adv through; also return {effective, notices} next to meta.
  - Source labels: label-only (attach to subsystem label / SourceGroup name where safe). Do
    NOT touch amplifier patch logic. Deep input routing is out of scope.
  VERIFY STAGE 1: write a quick script that (a) generates with adv=None for 220x450 and
  confirms identical output to current (same subsystem counts, integrity "ok"); (b) generates
  with mains boxes=12 and confirms 12/side; (c) a manual delay ring at 250 ft appears at 250 ft;
  (d) an out-of-range value clamps and emits a notice. The generated .dbpr must still have
  integrity "ok". DO NOT change engine default paths or NewProject_Skeleton.dbpr.

STAGE 2 — API (api/generate.py + lib/types.ts):
  - Accept optional "advanced" object (schema in the spec §3); validate/normalise it; convert
    ft->m as needed; pass adv into engine.generate.
  - Response adds "effective" and "notices" (may be empty for Simple mode). Keep base64 .dbpr
    delivery. Update lib/types.ts to match request + response exactly.
  VERIFY STAGE 2: curl POST with no "advanced" == current behaviour; curl with an "advanced"
  object returns notices + effective and a valid dbpr_base64 with meta.integrity "ok".

STAGE 3 — UI (app/):
  - Add a Simple/Advanced segmented toggle atop the form (match the existing units-toggle style).
  - Advanced view: width/depth/units, then collapsible sections Mains, Subs, Out fills, Front
    fills, Delays, Sources. PRE-FILL every field with the auto-derived value (fetch or compute
    defaults) so nothing is blank. Delays section: auto/manual switch; manual shows a small
    repeatable ring list (distance ft + boxes), add/remove, max 4.
  - POST includes the "advanced" object. Render "notices" as small amber inline notes near the
    relevant section. Plan/cards/parts stay as-is (they render whatever the engine returns).
  VERIFY STAGE 3: pnpm build compiles + type-checks clean; manually exercise a couple of
  overrides in the browser and confirm the plan/cards/parts update and notices show on clamp.

SHIP: commit in logical chunks with clear messages; push origin main (auto-deploys if the
GitHub<->Vercel link is connected, otherwise `vercel --prod`). Report the deployed URL and the
commit hashes. If the Vercel link still isn't connected, connect it in the dashboard.

HARD CONSTRAINTS: never modify a generated .dbpr after the engine writes it; don't delete/
regenerate NewProject_Skeleton.dbpr; engine default behaviour (adv=None) must be unchanged;
keep it stateless; keep lib/types.ts in sync with api/generate.py.
```

---

## Note for you (Joyjeet)

Stage 1 is the one to watch — it changes the engine, which we've guarded carefully. The
built-in Stage-1 verification (Simple mode unchanged + integrity "ok") is your safety net;
if Cursor reports that check failing, stop it and paste the result here before it proceeds to
API/UI. Once Stage 1 is green, the rest is low-risk form + plumbing work.
