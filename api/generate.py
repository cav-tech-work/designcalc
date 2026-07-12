"""DesignCalc engine API — Vercel Python serverless function.

POST /api/generate
  body: {
    "width_ft": number, "depth_ft": number, "units": "ft"|"m" (optional),
    "advanced": { ... }   // optional; omit = Simple mode (unchanged)
  }
  returns: {
    "design": { venue, subsystems[], parts[] },
    "meta":   { integrity, frame_angle, ... },
    "effective": { mains, subs, out_fills, front_fills, delays },
    "notices": [ { field, requested, applied, message } ],
    "dbpr_base64": "<base64 of the .dbpr file>",
    "filename": "DesignCalc_<depth>x<width>.dbpr"
  }

Stateless: generates into /tmp, reads it back for the summary, base64-encodes the
file into the JSON response, then discards it. Nothing is persisted.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import base64
import tempfile
import traceback

# make the bundled engine importable
_HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_HERE, "_engine"))

import engine          # noqa: E402  (the proven generator: generate())
import flatground_core as core  # noqa: E402
from summary import summarize    # noqa: E402
from adv import apply_source_labels  # noqa: E402

# input guardrails (feet) — keep within what the flat-ground engine handles safely
MIN_FT, MAX_W_FT, MAX_D_FT = 30.0, 800.0, 900.0

_META_KEYS = (
    "integrity", "frame_angle", "lowest_edge_ft", "mains_coverage_end_m",
    "coverage_end_is_estimate", "out_fills", "delay_rings", "venue",
)


def _validate(width_ft: float, depth_ft: float):
    errors = []
    if not (MIN_FT <= width_ft <= MAX_W_FT):
        errors.append(f"Width must be between {int(MIN_FT)} and {int(MAX_W_FT)} ft.")
    if not (MIN_FT <= depth_ft <= MAX_D_FT):
        errors.append(f"Depth must be between {int(MIN_FT)} and {int(MAX_D_FT)} ft.")
    return errors


def _norm_num(v):
    if v is None or v == "":
        return None
    return float(v)


def _norm_bool(v):
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    s = str(v).strip().lower()
    if s in ("true", "1", "yes", "on"):
        return True
    if s in ("false", "0", "no", "off"):
        return False
    return None


def _normalize_advanced(raw) -> dict | None:
    """Validate / normalise the optional advanced object. Returns None if absent/empty."""
    if not raw or not isinstance(raw, dict):
        return None
    adv: dict = {}

    mains = raw.get("mains")
    if isinstance(mains, dict):
        sec = {}
        if mains.get("spread_ft") is not None:
            sec["spread_ft"] = _norm_num(mains["spread_ft"])
        if mains.get("boxes_per_side") is not None:
            sec["boxes_per_side"] = _norm_num(mains["boxes_per_side"])
        if sec:
            adv["mains"] = sec

    subs = raw.get("subs")
    if isinstance(subs, dict):
        sec = {}
        if subs.get("stacks") is not None:
            sec["stacks"] = _norm_num(subs["stacks"])
        if subs.get("spacing_ft") is not None:
            sec["spacing_ft"] = _norm_num(subs["spacing_ft"])
        if sec:
            adv["subs"] = sec

    out_fills = raw.get("out_fills")
    if isinstance(out_fills, dict):
        sec = {}
        en = _norm_bool(out_fills.get("enabled"))
        if en is not None:
            sec["enabled"] = en
        if out_fills.get("boxes_per_side") is not None:
            sec["boxes_per_side"] = _norm_num(out_fills["boxes_per_side"])
        if sec:
            adv["out_fills"] = sec

    front_fills = raw.get("front_fills")
    if isinstance(front_fills, dict):
        sec = {}
        en = _norm_bool(front_fills.get("enabled"))
        if en is not None:
            sec["enabled"] = en
        if front_fills.get("count") is not None:
            sec["count"] = _norm_num(front_fills["count"])
        if sec:
            adv["front_fills"] = sec

    delays = raw.get("delays")
    if isinstance(delays, dict):
        mode = delays.get("mode") or "auto"
        if mode not in ("auto", "manual"):
            mode = "auto"
        sec: dict = {"mode": mode}
        if mode == "manual":
            rings_in = delays.get("rings") or []
            rings = []
            if isinstance(rings_in, list):
                for entry in rings_in[:4]:
                    if not isinstance(entry, dict) or entry.get("distance_ft") is None:
                        continue
                    ring = {"distance_ft": _norm_num(entry["distance_ft"])}
                    if entry.get("boxes_per_side") is not None:
                        ring["boxes_per_side"] = _norm_num(entry["boxes_per_side"])
                    rings.append(ring)
            sec["rings"] = rings
        adv["delays"] = sec

    sources = raw.get("sources")
    if isinstance(sources, dict) and sources:
        adv["sources"] = {
            str(k): str(v) for k, v in sources.items() if v is not None and str(v).strip()
        }

    return adv or None


def build(width_ft: float, depth_ft: float, advanced=None) -> dict:
    """Run the engine and assemble the full API payload."""
    out_dir = tempfile.mkdtemp(prefix="designcalc_")
    out_path = os.path.join(out_dir, f"DesignCalc_{int(depth_ft)}x{int(width_ft)}.dbpr")
    try:
        result = engine.generate(depth_ft, width_ft, out_path, adv=advanced)
        depth_m, width_m = depth_ft * core.FT, width_ft * core.FT
        design = summarize(out_path, width_m, depth_m)
        # Label-only source overrides also applied on the summary (id / role / label keys)
        if advanced and isinstance(advanced.get("sources"), dict):
            apply_source_labels(design, advanced["sources"])
        with open(out_path, "rb") as fh:
            dbpr_b64 = base64.b64encode(fh.read()).decode("ascii")
        meta = {k: result[k] for k in _META_KEYS if k in result}
        return {
            "design": design,
            "meta": meta,
            "effective": result.get("effective") or {},
            "notices": result.get("notices") or [],
            "dbpr_base64": dbpr_b64,
            "filename": os.path.basename(out_path),
        }
    finally:
        try:
            os.remove(out_path)
            os.rmdir(out_dir)
        except OSError:
            pass


class handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            data = json.loads(raw or b"{}")

            units = (data.get("units") or "ft").lower()
            width = float(data.get("width_ft"))
            depth = float(data.get("depth_ft"))
            if units == "m":  # convert incoming metres to feet for the engine
                width /= core.FT
                depth /= core.FT

            errors = _validate(width, depth)
            if errors:
                return self._send(400, {"error": "validation", "messages": errors})

            advanced = _normalize_advanced(data.get("advanced"))
            return self._send(200, build(width, depth, advanced=advanced))

        except (TypeError, ValueError):
            return self._send(400, {
                "error": "validation",
                "messages": ["Please enter numeric width and depth."],
            })
        except Exception as exc:  # noqa: BLE001
            return self._send(500, {
                "error": "engine",
                "message": "The design engine failed to generate this venue.",
                "detail": str(exc),
                "trace": traceback.format_exc(),
            })
