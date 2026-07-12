/** Client-side mirrors of flatground_core auto-defaults for Advanced form pre-fill. */

const FT = 0.3048;
const FRONT_OFFSET = 15 * FT;
const MAINS_X = 1.5;
const THROW_WINDOW = 68;
const MAINS_Y_MAX = 10.67;

function clamp(v: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, v));
}

function mainsCount(throwM: number) {
  return clamp(Math.round((16 * throwM) / THROW_WINDOW / 2) * 2, 6, 24);
}

function mainsY(widthM: number) {
  return Math.round(Math.min(MAINS_Y_MAX, widthM / 4) * 100) / 100;
}

function subStacks(widthM: number) {
  return clamp(Math.round((8 * widthM) / 46), 3, 14);
}

function ffCount(widthM: number) {
  return clamp(Math.round((6 * widthM) / 46 / 2) * 2, 4, 12);
}

/** Convert form width/depth in the selected units into feet. */
export function toFeet(value: number, units: "ft" | "m"): number {
  return units === "m" ? value / FT : value;
}

export interface AutoDefaults {
  mains: { spread_ft: number; boxes_per_side: number };
  subs: { stacks: number; spacing_ft: number };
  out_fills: { enabled: boolean; boxes_per_side: number };
  front_fills: { enabled: boolean; count: number };
  delays: {
    mode: "auto" | "manual";
    rings: { distance_ft: number; boxes_per_side: number }[];
  };
}

export function computeAutoDefaults(widthFt: number, depthFt: number): AutoDefaults {
  const widthM = widthFt * FT;
  const depthM = depthFt * FT;
  const far = FRONT_OFFSET + depthM;
  const throwM = Math.min(far - MAINS_X, THROW_WINDOW);
  const my = mainsY(widthM);
  const n = mainsCount(throwM);
  // delay1_from_mains_ft + overlap estimate (same idea as core)
  const delay1Ft = 185 + (n - 16) * 8.75;
  const overlapM = 17.5 * FT;
  const covEnd = Math.min(MAINS_X + delay1Ft * FT + overlapM, MAINS_X + throwM);
  const mainsReach = MAINS_X + throwM;
  const farEdge = FRONT_OFFSET + depthM;

  const rings: { distance_ft: number; boxes_per_side: number }[] = [];
  if (farEdge - mainsReach > 15) {
    let cov = covEnd;
    while (farEdge - cov > 12 && rings.length < 4) {
      const x = cov - overlapM;
      const farThrow = Math.min(farEdge - x, 40);
      rings.push({
        distance_ft: Math.round((x / FT) * 10) / 10,
        boxes_per_side: 8,
      });
      cov = x + farThrow;
    }
    const nr = rings.length;
    for (let i = 0; i < nr; i++) {
      rings[i].boxes_per_side = i === 0 && nr > 1 ? 10 : 8;
    }
  }

  return {
    mains: {
      spread_ft: Math.round(((my * 2) / FT) * 100) / 100,
      boxes_per_side: n,
    },
    subs: {
      stacks: subStacks(widthM),
      spacing_ft: 7,
    },
    out_fills: {
      enabled: widthM > 61,
      boxes_per_side: 10,
    },
    front_fills: {
      enabled: true,
      count: ffCount(widthM),
    },
    delays: {
      mode: "auto",
      rings,
    },
  };
}
