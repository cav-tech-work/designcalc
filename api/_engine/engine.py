#!/usr/bin/env python3
"""Generate a complete flat-ground d&b design from a venue size.

    python engine.py <depth_ft> <width_ft> [out.dbpr]

Flat-ground CORE (mains/subs/front fills) is always flatground_core.build_core() —
identical for every venue. Size only triggers out fills / delay rings (extensions.py).

Advanced mode: pass adv=dict(...) to override positional/quantity params. adv=None
keeps Simple-mode behaviour unchanged.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import flatground_core as core, extensions as ext
from writer import Writer
from adv import AdvState

SKELETON = os.path.join(os.path.dirname(__file__), "NewProject_Skeleton.dbpr")

def generate(depth_ft, width_ft, out_path, mains_variance_limit_ft=None, adv=None):
    D, W = depth_ft*core.FT, width_ft*core.FT
    state = AdvState(adv)
    w = Writer(SKELETON, out_path)
    vlim = mains_variance_limit_ft*core.FT if mains_variance_limit_ft else None
    info = core.build_core(w, D, W, vlim, adv=adv, state=state)
    of = ext.add_out_fills(w, W, info["mains_y_m"], adv=adv, state=state)
    rings = ext.add_delay_rings(
        w, D, W, info["coverage_end_m"], info["mains_reach_m"], adv=adv, state=state,
    )
    # ensure out_fills effective is set when auto path ran without section overrides
    if not state.effective.get("out_fills"):
        state.effective["out_fills"] = {
            "enabled": bool(of),
            "boxes_per_side": None,
        }
    w.write_floor(D, W); w.calibrate_spl(); w.patch_amplifiers()
    # Optional source labels: rename SourceGroups before integrity finalize (label-only).
    sources = state.section("sources") if isinstance(adv, dict) else {}
    # sources may be a flat map at adv["sources"] — AdvState.section expects nested dict;
    # for a flat map of labels, read directly:
    if isinstance(adv, dict) and isinstance(adv.get("sources"), dict):
        sources = adv["sources"]
        for role, label in sources.items():
            if not role or label is None:
                continue
            from adv import sanitize_label
            new = sanitize_label(label)
            if not new:
                continue
            # Match exact SourceGroup name (role), e.g. "Mains", "Delay 1"
            w.c.execute(
                "UPDATE SourceGroups SET Name=? WHERE Name=? AND Name!='Unused channels'",
                (new, str(role)),
            )
    ok = w.finalize()
    meta = dict(
        integrity=ok,
        frame_angle=info["frame_angle"],
        lowest_edge_ft=round(info["lowest_edge_ft"], 1),
        mains_coverage_end_m=info["coverage_end_m"],
        coverage_end_is_estimate=info["coverage_end_is_estimate"],
        out_fills=bool(of),
        delay_rings=rings,
        venue=f"{depth_ft}x{width_ft} ft ({D:.0f}x{W:.0f} m)",
        effective=state.effective,
        notices=list(state.notices),
    )
    return meta

if __name__ == "__main__":
    depth=float(sys.argv[1]); width=float(sys.argv[2])
    out=sys.argv[3] if len(sys.argv)>3 else f"Design_{int(depth)}x{int(width)}.dbpr"
    import json; print(json.dumps(generate(depth,width,out), indent=1))
    print("written:", out)
