"""Size-driven extensions — the ONLY additions around the flat-ground core, all via
the SAME shared line-array builder (core.build_line), so every house principle
(bottom height, count, frame angle, splay, gain-shade) applies to them too.

Rules (flat-ground): out fills only when width > 200 ft; delay rings past the
65-70 m throw window; each delay ring is ONE symmetric L/R paired source
(centre added only when width > 250 ft at the ring).

Advanced mode: optional `adv` / `state` overrides (enabled flags, box counts,
manual delay rings). Default path (adv=None) is unchanged.
"""
from __future__ import annotations
import flatground_core as core
C = 343.0

def add_out_fills(api, width_m, mains_y_m, adv=None, state=None):
    """Out fills only when width > 200 ft (61 m), unless Advanced overrides enabled."""
    from adv import AdvState
    state = state or AdvState(adv)
    of = state.section("out_fills")
    default_on = width_m > 61.0
    enabled = default_on if of.get("enabled") is None else bool(of["enabled"])
    if not enabled:
        state.effective["out_fills"] = {"enabled": False, "boxes_per_side": 0}
        return None
    n_override = None
    if of.get("boxes_per_side") is not None:
        n_override, _ = state.clamp_int(
            of["boxes_per_side"], 4, 16, "out_fills.boxes_per_side",
            "Out-fill boxes per side limited to 4–16 (V-Series).",
        )
    d = core.build_line(
        api, "Out Fills", "V-Series", 0.8, min(mains_y_m + 7, width_m / 3), 40.0,
        haim=10.0, level_offset=-3.0, n_override=n_override,
    )
    state.effective["out_fills"] = {
        "enabled": True,
        "boxes_per_side": d["n"],
    }
    return True

def add_delay_rings(api, depth_m, width_m, coverage_end_m, mains_reach_m, adv=None, state=None):
    """Cover past the throw window with delay rings. ONE symmetric L/R source per ring
    (centre only if width > 250 ft). Throw/count/frame/trim all from core.design().

    mode == "manual": place rings at user distances (clamped); otherwise auto (unchanged).
    """
    from adv import AdvState
    state = state or AdvState(adv)
    delays = state.section("delays")
    mode = delays.get("mode") or "auto"
    if mode == "manual":
        return _add_delay_rings_manual(
            api, depth_m, width_m, mains_reach_m, delays, state,
        )
    return _add_delay_rings_auto(
        api, depth_m, width_m, coverage_end_m, mains_reach_m, state,
    )

def _add_delay_rings_auto(api, depth_m, width_m, coverage_end_m, mains_reach_m, state):
    """Original auto delay placement — behaviour must stay identical to pre-Advanced."""
    OVERLAP = core.OVERLAP_M     # ring sits 15-20 ft before the current coverage end
    DELAY_THROW = 40.0
    far_edge = core.FRONT_OFFSET + depth_m
    DELAY_TRIGGER = 15.0   # add delays only if audience extends > ~15 m past mains' usable reach
    if far_edge - mains_reach_m <= DELAY_TRIGGER:
        state.effective["delays"] = {"mode": "auto", "rings": []}
        return []          # mains (with acceptable droop) cover it -> no delays (e.g. Test_v1)
    # look-ahead: work out ring positions first so we know how many there are
    positions=[]; cov=coverage_end_m
    while far_edge - cov > 12 and len(positions) < 4:
        x = round(cov - OVERLAP, 2); far = min(far_edge - x, DELAY_THROW)
        positions.append((x, far)); cov = round(x + far, 2)   # delays hold ~full throw (reviewed: ~40 m/ring)
    nrings = len(positions)
    # system rule: 1 ring -> V; multiple -> Delay 1 = KSL (biggest throw), rest = V
    rings=[]; yc = core.mains_y(width_m)
    for i,(x,far) in enumerate(positions, 1):
        system = "KSL" if (i == 1 and nrings > 1) else "V-Series"
        dly = round((x-1.5)/C, 4)
        loff=-3.0*i                                                                 # D1 -3, D2 -6, ... (level-match at hand-off)
        d = core.build_line(api, f"Delay {i}", system, x, yc, far, delay=dly, level_offset=loff)   # ONE symmetric L/R
        if width_m > core.LCR_WIDTH_M:                                             # centre only past 250 ft
            core.build_line(api, f"Delay {i} C", system, x, 0.0, far, delay=dly, paired=False, level_offset=loff)
        rings.append(dict(ring=i, x_m=x, system=system, delay_ms=round(dly*1000),
                          covers_to_m=round(x + far, 2),
                          lcr=width_m>core.LCR_WIDTH_M,
                          boxes_per_side=d["n"]))
    state.effective["delays"] = {
        "mode": "auto",
        "rings": [
            {"distance_ft": round(r["x_m"] / core.FT, 1), "boxes_per_side": r["boxes_per_side"]}
            for r in rings
        ],
    }
    # strip helper key before returning meta-facing rings
    for r in rings:
        r.pop("boxes_per_side", None)
    return rings

def _add_delay_rings_manual(api, depth_m, width_m, mains_reach_m, delays, state):
    DELAY_THROW = 40.0
    far_edge = core.FRONT_OFFSET + depth_m
    lo_ft = mains_reach_m / core.FT
    hi_ft = max(lo_ft, (far_edge - 12.0) / core.FT)
    raw = delays.get("rings") or []
    if not isinstance(raw, list):
        raw = []
    raw = raw[:4]
    # first pass: clamp distances so we know nrings for the system rule
    planned = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict) or entry.get("distance_ft") is None:
            continue
        dist_ft, _ = state.clamp(
            entry["distance_ft"], lo_ft, hi_ft,
            f"delays.rings[{i}].distance_ft",
            "Delay ring distance limited to between mains reach and the far edge.",
        )
        n_override = None
        if entry.get("boxes_per_side") is not None:
            n_override, _ = state.clamp_int(
                entry["boxes_per_side"], 4, 16,
                f"delays.rings[{i}].boxes_per_side",
                "Delay boxes per side limited to 4–16.",
            )
        planned.append((dist_ft, n_override, i))

    nrings = len(planned)
    rings = []
    yc = core.mains_y(width_m)
    eff_rings = []
    for idx, (dist_ft, n_override, _src_i) in enumerate(planned, 1):
        x = round(dist_ft * core.FT, 2)
        far = min(far_edge - x, DELAY_THROW)
        if far <= 1.0:
            far = 1.0
        system = "KSL" if (idx == 1 and nrings > 1) else "V-Series"
        dly = round((x - 1.5) / C, 4)
        loff = -3.0 * idx
        d = core.build_line(
            api, f"Delay {idx}", system, x, yc, far,
            delay=dly, level_offset=loff, n_override=n_override,
        )
        if width_m > core.LCR_WIDTH_M:
            core.build_line(
                api, f"Delay {idx} C", system, x, 0.0, far,
                delay=dly, paired=False, level_offset=loff, n_override=n_override,
            )
        rings.append(dict(
            ring=idx, x_m=x, system=system, delay_ms=round(dly * 1000),
            covers_to_m=round(x + far, 2),
            lcr=width_m > core.LCR_WIDTH_M,
        ))
        eff_rings.append({
            "distance_ft": round(dist_ft, 1),
            "boxes_per_side": d["n"],
        })
    state.effective["delays"] = {"mode": "manual", "rings": eff_rings}
    return rings
