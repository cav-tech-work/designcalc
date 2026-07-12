"""Advanced-mode helpers — clamp + notice recording. Additive; unused when adv is None."""
from __future__ import annotations


class AdvState:
    """Mutable bag of notices + effective values collected during a generate() call."""

    def __init__(self, adv=None):
        self.adv = adv if isinstance(adv, dict) else {}
        self.notices: list[dict] = []
        self.effective: dict = {
            "mains": {},
            "subs": {},
            "out_fills": {},
            "front_fills": {},
            "delays": {},
        }

    def section(self, name: str) -> dict:
        sec = self.adv.get(name)
        return sec if isinstance(sec, dict) else {}

    def clamp(self, value, lo, hi, field, message=None):
        """Clamp a numeric value; append a notice if it moved. Returns (applied, notice_or_None)."""
        requested = float(value)
        applied = max(float(lo), min(float(hi), requested))
        notice = None
        if abs(applied - requested) > 1e-9:
            notice = {
                "field": field,
                "requested": requested,
                "applied": applied,
                "message": message
                or f"{field} limited to the safe range {lo}–{hi}.",
            }
            self.notices.append(notice)
        return applied, notice

    def clamp_int(self, value, lo, hi, field, message=None):
        requested = float(value)
        applied = int(round(max(float(lo), min(float(hi), requested))))
        # keep applied inside bounds after rounding
        applied = max(int(lo), min(int(hi), applied))
        notice = None
        if abs(applied - requested) > 1e-9:
            notice = {
                "field": field,
                "requested": requested,
                "applied": applied,
                "message": message
                or f"{field} limited to the safe range {lo}–{hi}.",
            }
            self.notices.append(notice)
        return applied, notice

    def clamp_even(self, value, lo, hi, field, message=None):
        """Clamp to [lo, hi] then snap to even (for front-fill counts)."""
        applied, _ = self.clamp_int(value, lo, hi, field, message)
        if applied % 2 != 0:
            # prefer stepping down when possible
            even = applied - 1 if applied - 1 >= int(lo) else applied + 1
            even = max(int(lo), min(int(hi), even))
            if even % 2 != 0:
                even = int(lo) if int(lo) % 2 == 0 else int(lo) + 1
            notice = {
                "field": field,
                "requested": float(value),
                "applied": even,
                "message": message
                or f"{field} must be an even count between {lo} and {hi}.",
            }
            self.notices.append(notice)
            return even, notice
        return applied, None


def sanitize_label(text) -> str:
    if text is None:
        return ""
    s = "".join(ch for ch in str(text) if ch.isprintable()).strip()
    return s[:80]


def apply_source_labels(design: dict, sources: dict | None) -> None:
    """Override display / source labels in the summary (does not rewrite the .dbpr)."""
    if not sources or not isinstance(sources, dict):
        return
    for ss in design.get("subsystems") or []:
        candidates = (
            ss.get("id"),
            ss.get("role"),
            ss.get("label"),
            f"{ss.get('role')} {ss.get('side')}".strip(),
        )
        for key in candidates:
            if key and key in sources:
                label = sanitize_label(sources[key])
                if label:
                    ss["label"] = label
                    ss["source_label"] = label
                break
