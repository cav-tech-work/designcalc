#!/usr/bin/env python3
"""Generate a complete flat-ground d&b design from a venue size.

    python generate.py <depth_ft> <width_ft> [out.dbpr]

Flat-ground CORE (mains/subs/front fills) is always flatground_core.build_core() —
identical for every venue. Size only triggers out fills / delay rings (extensions.py).
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import flatground_core as core, extensions as ext
from writer import Writer

SKELETON = os.path.join(os.path.dirname(__file__), "NewProject_Skeleton.dbpr")

def generate(depth_ft, width_ft, out_path, mains_variance_limit_ft=None):
    D, W = depth_ft*core.FT, width_ft*core.FT
    w = Writer(SKELETON, out_path)
    vlim = mains_variance_limit_ft*core.FT if mains_variance_limit_ft else None
    info = core.build_core(w, D, W, vlim)    # <-- flat-ground core: principles fixed, quantities scale
    of = ext.add_out_fills(w, W, info["mains_y_m"])   # rule: width > 200 ft
    rings = ext.add_delay_rings(w, D, W, info["coverage_end_m"], info["mains_reach_m"])   # add if past usable reach; position from coverage end
    w.write_floor(D, W); w.calibrate_spl(); w.patch_amplifiers()
    ok = w.finalize()
    return dict(integrity=ok, frame_angle=info["frame_angle"], lowest_edge_ft=round(info["lowest_edge_ft"],1),
                mains_coverage_end_m=info["coverage_end_m"], coverage_end_is_estimate=info["coverage_end_is_estimate"],
                out_fills=bool(of), delay_rings=rings, venue=f"{depth_ft}x{width_ft} ft ({D:.0f}x{W:.0f} m)")

if __name__ == "__main__":
    depth=float(sys.argv[1]); width=float(sys.argv[2])
    out=sys.argv[3] if len(sys.argv)>3 else f"Design_{int(depth)}x{int(width)}.dbpr"
    import json; print(json.dumps(generate(depth,width,out), indent=1))
    print("written:", out)
