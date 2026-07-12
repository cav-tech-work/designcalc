"""Read a generated .dbpr and produce the design summary the frontend renders.

The file is the single source of truth: the preview, subsystem cards, and parts
list are all derived from what actually got written, so they can never drift from
the downloadable .dbpr.
"""
from __future__ import annotations
import sqlite3

# meters -> feet for display
M_TO_FT = 1 / 0.3048


def _side(origin_y: float) -> str:
    # engine convention: +Y = stage-left, -Y = stage-right, 0 = centre
    if origin_y > 0.05:
        return "L"
    if origin_y < -0.05:
        return "R"
    return "C"


def summarize(dbpr_path: str, width_m: float, depth_m: float,
              front_off_m: float = 15 * 0.3048) -> dict:
    c = sqlite3.connect(f"file:{dbpr_path}?mode=ro", uri=True).cursor()

    # --- subsystems (one per SourceGroup that has cabinets) ---
    rows = c.execute(
        """
        SELECT sg.SourceGroupId, sg.Name, sg.RelativeDelay,
               sgad.System, sgad.OriginX, sgad.OriginY,
               sgad.VerticalAimingAngle, sgad.HeightLowestEdge,
               (SELECT COUNT(*) FROM Cabinets WHERE SourceGroupId = sg.SourceGroupId)
        FROM SourceGroups sg
        JOIN SourceGroupsAdditionalData sgad ON sgad.SourceGroupId = sg.SourceGroupId
        WHERE sg.Name != 'Unused channels'
        ORDER BY sg.SourceGroupId
        """
    ).fetchall()

    subsystems = []
    for sgid, name, rel_delay, system, ox, oy, aim, low_edge, count in rows:
        if not count:
            continue
        side = _side(oy or 0.0)
        label = name if side == "C" else f"{name} {side}"
        subsystems.append({
            "id": f"sg_{sgid}",
            "role": name,
            "side": side,
            "label": label,
            "box_model": system,
            "box_count": count,
            "position": {
                "depth_m": round(ox or 0.0, 2),
                "lateral_m": round(oy or 0.0, 2),
                "depth_ft": round((ox or 0.0) * M_TO_FT, 1),
                "lateral_ft": round((oy or 0.0) * M_TO_FT, 1),
            },
            "aim_deg": round(aim, 1) if aim is not None else None,
            "lowest_edge_ft": round((low_edge or 0.0) * M_TO_FT, 1) if low_edge else None,
            "delay_ms": round(rel_delay, 1) if rel_delay else None,
            # sources aren't stored as distinct entities in the file; label by role+side
            "source_label": label,
        })

    # --- parts list (bill of materials) ---
    parts = []

    # loudspeakers by model
    box_rows = c.execute(
        """
        SELECT sgad.System, COUNT(*)
        FROM Cabinets cab
        JOIN SourceGroupsAdditionalData sgad ON sgad.SourceGroupId = cab.SourceGroupId
        JOIN SourceGroups sg ON sg.SourceGroupId = cab.SourceGroupId
        WHERE sg.Name != 'Unused channels'
        GROUP BY sgad.System
        ORDER BY COUNT(*) DESC
        """
    ).fetchall()
    for model, qty in box_rows:
        parts.append({"category": "Loudspeakers", "item": model, "qty": qty})

    # amplifiers by model
    for model, qty in c.execute(
        "SELECT Model, COUNT(*) FROM Devices GROUP BY Model ORDER BY COUNT(*) DESC"
    ).fetchall():
        parts.append({"category": "Amplifiers", "item": model, "qty": qty})

    # flying frames by display name / type
    frame_rows = c.execute(
        "SELECT COALESCE(NULLIF(DisplayName,''), Name, Type), COUNT(*) "
        "FROM FlyingFrames GROUP BY 1 ORDER BY COUNT(*) DESC"
    ).fetchall()
    for fname, qty in frame_rows:
        if fname:
            parts.append({"category": "Rigging", "item": str(fname), "qty": qty})

    return {
        "venue": {
            "width_ft": round(width_m * M_TO_FT, 1),
            "depth_ft": round(depth_m * M_TO_FT, 1),
            "width_m": round(width_m, 2),
            "depth_m": round(depth_m, 2),
            "front_offset_m": round(front_off_m, 2),
        },
        "subsystems": subsystems,
        "parts": parts,
    }
