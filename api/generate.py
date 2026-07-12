"""DesignCalc engine API — Vercel Python serverless function.

POST /api/generate
  body: { "width_ft": number, "depth_ft": number, "units": "ft"|"m" (optional) }
  returns: {
    "design": { venue, subsystems[], parts[] },
    "meta":   { frame_angle, lowest_edge_ft, out_fills, delay_rings, ... },
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

# input guardrails (feet) — keep within what the flat-ground engine handles safely
MIN_FT, MAX_W_FT, MAX_D_FT = 30.0, 800.0, 900.0


def _validate(width_ft: float, depth_ft: float):
    errors = []
    if not (MIN_FT <= width_ft <= MAX_W_FT):
        errors.append(f"Width must be between {int(MIN_FT)} and {int(MAX_W_FT)} ft.")
    if not (MIN_FT <= depth_ft <= MAX_D_FT):
        errors.append(f"Depth must be between {int(MIN_FT)} and {int(MAX_D_FT)} ft.")
    return errors


def build(width_ft: float, depth_ft: float) -> dict:
    """Run the engine and assemble the full API payload."""
    out_dir = tempfile.mkdtemp(prefix="designcalc_")
    out_path = os.path.join(out_dir, f"DesignCalc_{int(depth_ft)}x{int(width_ft)}.dbpr")
    try:
        meta = engine.generate(depth_ft, width_ft, out_path)
        depth_m, width_m = depth_ft * core.FT, width_ft * core.FT
        design = summarize(out_path, width_m, depth_m)
        with open(out_path, "rb") as fh:
            dbpr_b64 = base64.b64encode(fh.read()).decode("ascii")
        return {
            "design": design,
            "meta": meta,
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

            return self._send(200, build(width, depth))

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
