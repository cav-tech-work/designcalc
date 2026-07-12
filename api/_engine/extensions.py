"""Size-driven extensions — the ONLY additions around the flat-ground core, all via
the SAME shared line-array builder (core.build_line), so every house principle
(bottom height, count, frame angle, splay, gain-shade) applies to them too.

Rules (flat-ground): out fills only when width > 200 ft; delay rings past the
65-70 m throw window; each delay ring is ONE symmetric L/R paired source
(centre added only when width > 250 ft at the ring)."""
from __future__ import annotations
import flatground_core as core
C = 343.0

def add_out_fills(api, width_m, mains_y_m):
    """Out fills only when width > 200 ft (61 m). Paired, aimed +/-35, own house geometry."""
    if width_m <= 61.0: return None
    core.build_line(api, "Out Fills", "V-Series", 0.8, min(mains_y_m+7, width_m/3), 40.0, haim=10.0, level_offset=-3.0)  # low, slightly-out, -3 dB to match mains
    return True

def add_delay_rings(api, depth_m, width_m, coverage_end_m, mains_reach_m):
    """Cover past the throw window with delay rings. ONE symmetric L/R source per ring
    (centre only if width > 250 ft). Throw/count/frame/trim all from core.design()."""
    OVERLAP = core.OVERLAP_M     # ring sits 15-20 ft before the current coverage end
    DELAY_THROW = 40.0
    far_edge = core.FRONT_OFFSET + depth_m
    DELAY_TRIGGER = 15.0   # add delays only if audience extends > ~15 m past mains' usable reach
    if far_edge - mains_reach_m <= DELAY_TRIGGER:
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
        core.build_line(api, f"Delay {i}", system, x, yc, far, delay=dly, level_offset=loff)   # ONE symmetric L/R
        if width_m > core.LCR_WIDTH_M:                                             # centre only past 250 ft
            core.build_line(api, f"Delay {i} C", system, x, 0.0, far, delay=dly, paired=False, level_offset=loff)
        rings.append(dict(ring=i, x_m=x, system=system, delay_ms=round(dly*1000),
                          covers_to_m=round(x + far, 2),
                          lcr=width_m>core.LCR_WIDTH_M))
    return rings
