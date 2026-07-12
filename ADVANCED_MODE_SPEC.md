# DesignCalc — Advanced Mode spec (roadmap #1)

**Status:** approved to build. **Owner:** Joyjeet. **PM/spec:** Claude.
Builds on the live Simple-mode MVP. Read `CLAUDE.md` and `PRD_DesignCalc.md` first.

---

## 1. Concept

Advanced mode = Simple mode + user overrides of what the engine auto-derives. Same engine,
same `.dbpr` correctness, same acceptance test.

**Override philosophy (approved: HYBRID):**
- **Positional / quantity params are HARD overrides** — the engine uses the user's numbers
  (mains spread, delay ring distances, box counts, sub/fill counts, toggles, source labels).
- **Acoustically-risky params stay GUIDED** — frame angle, splay, trim remain engine-derived
  from the (possibly overridden) box count and throw. The user never hand-sets these in v1.
- Every hard override is still **clamped to a safety range** (product min/max, physical venue
  bounds). When a value is clamped, the response reports it and the UI shows a note. This is
  what keeps designs valid and the ArrayCalc acceptance test intact.

**UX rule:** the Advanced form is **pre-filled with the auto-derived Simple-mode values**.
A field left untouched = house-style default; a changed field = the user's override. Never a
blank form.

## 2. Controls in this release (all four approved)

| Group | Field | Type | Default (auto) | Clamp / guard |
|---|---|---|---|---|
| **Mains** | L/R spread (ft, centre-to-centre) | hard | `2 × min(35 ft, width/4)` | keep both hangs inside the audience width; ≤ `width − margin` |
| | boxes per side | hard | `mains_count(throw)` | 6–24 (KSL min/max) |
| **Subs** | stack count | hard | `sub_stacks(width)` | 3–14 |
| | spacing (ft, c-c) | hard | 7 ft | 5–8 ft |
| **Out fills** | enabled | hard | on if width > 200 ft | — |
| | boxes per side | hard | engine value | 4–16 (V min/max) |
| **Front fills** | enabled | hard | on | — |
| | count | hard | `ff_count(width)` | even, 4–12 |
| **Delays** | mode | hard | auto | auto \| manual |
| | (manual) ring: distance from stage (ft) | hard | auto look-ahead | between mains reach and `depth − ~40 ft`; max 4 rings |
| | (manual) ring: boxes per side | hard | engine value | 4–16 |
| **Sources** | input source label per subsystem | hard | role+side (e.g. "Mains L") | free text, sanitised; see §6 note |

Anything not listed (frame angle, splay, trim, CPL/HFC/CUT, sub dispersion) stays fully
engine-controlled in v1.

## 3. API contract change

`POST /api/generate` gains an optional `advanced` object. Omit it → identical to Simple mode.

```
{
  "width_ft": number,
  "depth_ft": number,
  "units": "ft" | "m",
  "advanced": {                         // optional; any field may be null/absent = auto
    "mains":       { "spread_ft": number|null, "boxes_per_side": number|null },
    "subs":        { "stacks": number|null, "spacing_ft": number|null },
    "out_fills":   { "enabled": boolean|null, "boxes_per_side": number|null },
    "front_fills": { "enabled": boolean|null, "count": number|null },
    "delays": {
      "mode": "auto" | "manual",
      "rings": [ { "distance_ft": number, "boxes_per_side": number|null } ]   // manual only
    },
    "sources": { "<subsystem_id_or_role>": "label", ... }
  }
}
```

**Response** gains two fields (Simple-mode responses may leave `overrides`/`notices` empty):

```
{
  "design": { ...unchanged (venue, subsystems[], parts[]) },
  "meta":   { ...unchanged },
  "effective": {                       // the values actually used after clamping
    "mains": {...}, "subs": {...}, "out_fills": {...}, "front_fills": {...}, "delays": {...}
  },
  "notices": [                         // one per clamp / ignored input, for the UI
    { "field": "mains.spread_ft", "requested": 260, "applied": 200,
      "message": "Mains spread limited to keep both hangs inside the audience width." }
  ],
  "dbpr_base64": "...",
  "filename": "..."
}
```

The frontend must render `notices` (small amber inline notes) and may show `effective`
values so the user sees what was actually applied.

## 4. Engine changes (additive, Simple mode unaffected)

All changes are **optional parameters defaulting to current behaviour**. Do NOT change any
existing default path. Add a small clamp helper that records notices.

Signatures (in `api/_engine/`):

- `flatground_core.design(system, throw, n_override=None)`
  → if `n_override`, use it as `n` (instead of `mains_count`); recompute `splays =
  deep_j_splay(n)`, `levels = mains_levels(n)`, `arr_h`, `le`, `fa`, `z` from that n.
  Frame/trim stay derived (guided).
- `flatground_core.build_line(..., n_override=None)` → pass through to `design`.
- `flatground_core.build_core(api, depth_m, width_m, mains_variance_limit_m=None, adv=None)`
  - mains spread → `my = clamp(adv.mains.spread_ft/2 · FT, min≈2 m, width_m/2 − 0.5)`;
    else `mains_y(width_m)`.
  - mains boxes → `n_override = clamp(adv.mains.boxes_per_side, 6, 24)`.
- `flatground_core.build_sub_array(api, width_m, adv=None)` → override `ns`
  (clamp 3–14) and `SUB_SPACING` (clamp 5–8 ft).
- `flatground_core.build_front_fills(api, width_m, mains_y_m, adv=None)` → `enabled`
  gate; `nff = clamp_even(count, 4, 12)`.
- `extensions.add_out_fills(api, width_m, mains_y_m, adv=None)` → `enabled` overrides the
  width>61 m rule; `boxes_per_side` via `n_override` (clamp 4–16).
- `extensions.add_delay_rings(api, depth_m, width_m, coverage_end_m, mains_reach_m, adv=None)`
  - `mode == "manual"`: place one symmetric ring per entry at `x = distance_ft · FT`
    (clamp within `mains_reach_m … far_edge − ~12 m`, max 4), `boxes_per_side` via
    `n_override`; keep the existing system rule (ring 1 = KSL if >1 ring, else V) and delay
    time `dly = (x − 1.5)/343`.
  - `mode == "auto"` or absent: current behaviour, unchanged.
- `engine.generate(depth_ft, width_ft, out_path, mains_variance_limit_ft=None, adv=None)`
  → thread `adv` through; return `effective` + `notices` alongside the existing `meta`.

**Source labels (§6 note):** in v1, a source label is stored as the subsystem's display
label (carried into the design summary and shown on cards) and appended to the SourceGroup
name where safe. Deep input-routing into the `.dbpr` patch (named analog/Dante inputs) is
**out of scope for v1** — analog inputs are implicit in the file; full routing is a later
enhancement. Keep this label-only so we don't touch the amplifier patch logic.

## 5. Frontend changes

- Add a **Simple / Advanced** toggle at the top of the form (segmented control, matches the
  existing units toggle style).
- **Simple** = today's form (width, depth, units).
- **Advanced** = the same width/depth/units, then collapsible sections: **Mains**, **Subs**,
  **Out fills**, **Front fills**, **Delays**, **Sources**. Each field pre-filled with the
  auto value. Delays section has an auto/manual switch; manual reveals a small repeatable
  ring list (distance + boxes, add/remove, max 4).
- On generate, POST includes the `advanced` object (only the sections the user expanded/
  changed need to be sent; unchanged = omit or send nulls).
- Render `notices` as amber inline notes near the relevant section; keep the plan, cards and
  parts exactly as they are (they already render whatever the engine returns).
- Keep `lib/types.ts` in sync with the new request/response fields.

## 6. Acceptance criteria

1. Simple mode is byte-for-byte unchanged (no `advanced` → same output as today).
2. Each override changes the design as expected (e.g. mains boxes 16→12 yields 12/side; a
   manual delay ring at 250 ft appears at 250 ft).
3. Out-of-range inputs are clamped, the `.dbpr` still opens in ArrayCalc with **no warning /
   no password**, and a `notice` explains each clamp.
4. `pnpm build` compiles + type-checks clean; `lib/types.ts` matches the API.
5. Engine defaults untouched; no change to `NewProject_Skeleton.dbpr`; still stateless.

## 7. Out of scope (later)

Hand-set frame angle/splay; per-box editing; deep input-source routing into the patch;
saving/loading advanced presets; drag-to-reposition on the plan.
