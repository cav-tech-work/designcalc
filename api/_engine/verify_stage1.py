#!/usr/bin/env python3
"""Stage-1 Advanced mode verification.

(a) adv=None @ 220x450 matches baseline subsystem counts + integrity ok
(b) mains boxes=12 yields 12/side
(c) manual delay ring at 250 ft appears near 250 ft
(d) out-of-range value clamps and emits a notice; integrity still ok
"""
from __future__ import annotations
import os
import sys
import tempfile
import sqlite3

sys.path.insert(0, os.path.dirname(__file__))
import engine
from summary import summarize
import flatground_core as core

FT = core.FT
W, D = 220.0, 450.0


def _counts(path):
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True).cursor()
    rows = c.execute(
        """
        SELECT sg.Name, COUNT(*)
        FROM Cabinets cab
        JOIN SourceGroups sg ON sg.SourceGroupId = cab.SourceGroupId
        WHERE sg.Name != 'Unused channels'
        GROUP BY sg.Name
        ORDER BY sg.Name
        """
    ).fetchall()
    return {name: qty for name, qty in rows}


def _mains_boxes_per_side(path):
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True).cursor()
    # one side of Mains (paired L/R share the same Name)
    n = c.execute(
        """
        SELECT COUNT(*) FROM Cabinets cab
        JOIN SourceGroups sg ON sg.SourceGroupId = cab.SourceGroupId
        WHERE sg.Name = 'Mains'
        """
    ).fetchone()[0]
    return n // 2  # L+R


def _delay_depths_ft(path):
    design = summarize(path, W * FT, D * FT)
    out = []
    for ss in design["subsystems"]:
        if str(ss["role"]).startswith("Delay") and ss["side"] in ("L", "R", "C"):
            # one entry per ring (use R or first)
            if ss["side"] == "R" or (ss["side"] == "C" and not any(
                x["role"] == ss["role"] and x["side"] == "R" for x in design["subsystems"]
            )):
                out.append((ss["role"], ss["position"]["depth_ft"]))
    return out


def run():
    tmp = tempfile.mkdtemp(prefix="dc_stage1_")
    base = os.path.join(tmp, "base.dbpr")
    a = os.path.join(tmp, "a.dbpr")
    b = os.path.join(tmp, "b.dbpr")
    cpath = os.path.join(tmp, "c.dbpr")
    dpath = os.path.join(tmp, "d.dbpr")

    print("=== (a) adv=None baseline ===")
    meta_a1 = engine.generate(D, W, base, adv=None)
    meta_a2 = engine.generate(D, W, a, adv=None)
    assert meta_a1["integrity"] == "ok", meta_a1
    assert meta_a2["integrity"] == "ok", meta_a2
    assert meta_a2.get("notices") == [], meta_a2.get("notices")
    c1, c2 = _counts(base), _counts(a)
    assert c1 == c2, (c1, c2)
    print("  integrity ok; subsystem cabinet counts identical:", c1)

    print("=== (b) mains boxes_per_side=12 ===")
    meta_b = engine.generate(D, W, b, adv={"mains": {"boxes_per_side": 12}})
    assert meta_b["integrity"] == "ok", meta_b
    n = _mains_boxes_per_side(b)
    assert n == 12, f"expected 12/side, got {n}"
    assert meta_b["effective"]["mains"]["boxes_per_side"] == 12
    print(f"  mains boxes/side = {n}; integrity ok")

    print("=== (c) manual delay ring at 250 ft ===")
    meta_c = engine.generate(D, W, cpath, adv={
        "delays": {
            "mode": "manual",
            "rings": [{"distance_ft": 250, "boxes_per_side": 8}],
        }
    })
    assert meta_c["integrity"] == "ok", meta_c
    depths = _delay_depths_ft(cpath)
    assert depths, "no delay rings found"
    # closest ring to 250 ft should be within ~1 ft
    nearest = min(abs(d - 250.0) for _, d in depths)
    assert nearest < 1.5, f"expected ~250 ft, got {depths}"
    print(f"  delay depths ft: {depths}; nearest delta={nearest:.2f}")

    print("=== (d) out-of-range clamp + notice ===")
    meta_d = engine.generate(D, W, dpath, adv={
        "mains": {"boxes_per_side": 99},  # clamp to 24
    })
    assert meta_d["integrity"] == "ok", meta_d
    assert meta_d["notices"], "expected a clamp notice"
    n = _mains_boxes_per_side(dpath)
    assert n == 24, f"expected clamp to 24, got {n}"
    fields = [x["field"] for x in meta_d["notices"]]
    assert "mains.boxes_per_side" in fields, meta_d["notices"]
    print(f"  clamped to {n}; notices={meta_d['notices']}")

    print("\nSTAGE 1 PASS")


if __name__ == "__main__":
    run()
