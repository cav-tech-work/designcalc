"use client";

import { Notice, Effective, Units } from "@/lib/types";
import {
  AutoDefaults,
  convertLenString,
  formatLenFromFt,
  fromFeet,
  toFeet,
} from "@/lib/defaults";

export interface AdvFormState {
  mainsSpread: string;
  mainsBoxes: string;
  subStacks: string;
  subSpacing: string;
  outEnabled: boolean;
  outBoxes: string;
  ffEnabled: boolean;
  ffCount: string;
  delayMode: "auto" | "manual";
  rings: { distance: string; boxes_per_side: string }[];
  sources: Record<string, string>;
}

export function defaultsToForm(d: AutoDefaults, units: Units = "ft"): AdvFormState {
  return {
    mainsSpread: formatLenFromFt(d.mains.spread_ft, units),
    mainsBoxes: String(d.mains.boxes_per_side),
    subStacks: String(d.subs.stacks),
    subSpacing: formatLenFromFt(d.subs.spacing_ft, units),
    outEnabled: d.out_fills.enabled,
    outBoxes: String(d.out_fills.boxes_per_side),
    ffEnabled: d.front_fills.enabled,
    ffCount: String(d.front_fills.count),
    delayMode: d.delays.mode,
    rings: d.delays.rings.map((r) => ({
      distance: formatLenFromFt(r.distance_ft, units),
      boxes_per_side: String(r.boxes_per_side),
    })),
    sources: {},
  };
}

export function effectiveToForm(
  eff: Effective,
  prev: AdvFormState,
  units: Units = "ft",
): AdvFormState {
  const next = { ...prev };
  if (eff.mains?.spread_ft != null) next.mainsSpread = formatLenFromFt(eff.mains.spread_ft, units);
  if (eff.mains?.boxes_per_side != null) next.mainsBoxes = String(eff.mains.boxes_per_side);
  if (eff.subs?.stacks != null) next.subStacks = String(eff.subs.stacks);
  if (eff.subs?.spacing_ft != null) next.subSpacing = formatLenFromFt(eff.subs.spacing_ft, units);
  if (eff.out_fills?.enabled != null) next.outEnabled = eff.out_fills.enabled;
  if (eff.out_fills?.boxes_per_side != null) {
    next.outBoxes = String(eff.out_fills.boxes_per_side);
  }
  if (eff.front_fills?.enabled != null) next.ffEnabled = eff.front_fills.enabled;
  if (eff.front_fills?.count != null) next.ffCount = String(eff.front_fills.count);
  if (eff.delays?.mode) next.delayMode = eff.delays.mode;
  if (eff.delays?.rings) {
    next.rings = eff.delays.rings.map((r) => ({
      distance: formatLenFromFt(r.distance_ft, units),
      boxes_per_side: String(r.boxes_per_side),
    }));
  }
  return next;
}

/** Convert length fields in the advanced form when the units toggle changes. */
export function convertAdvFormUnits(form: AdvFormState, from: Units, to: Units): AdvFormState {
  if (from === to) return form;
  return {
    ...form,
    mainsSpread: convertLenString(form.mainsSpread, from, to),
    subSpacing: convertLenString(form.subSpacing, from, to),
    rings: form.rings.map((r) => ({
      ...r,
      distance: convertLenString(r.distance, from, to),
    })),
  };
}

function num(s: string): number | null {
  const v = parseFloat(s);
  return Number.isFinite(v) ? v : null;
}

/** Build the API `advanced` object; length fields are always sent in feet. */
export function formToAdvanced(form: AdvFormState, units: Units = "ft") {
  const lenFt = (s: string) => {
    const v = num(s);
    return v == null ? null : toFeet(v, units);
  };
  const advanced: Record<string, unknown> = {
    mains: {
      spread_ft: lenFt(form.mainsSpread),
      boxes_per_side: num(form.mainsBoxes),
    },
    subs: {
      stacks: num(form.subStacks),
      spacing_ft: lenFt(form.subSpacing),
    },
    out_fills: {
      enabled: form.outEnabled,
      boxes_per_side: form.outEnabled ? num(form.outBoxes) : null,
    },
    front_fills: {
      enabled: form.ffEnabled,
      count: form.ffEnabled ? num(form.ffCount) : null,
    },
    delays: {
      mode: form.delayMode,
      rings:
        form.delayMode === "manual"
          ? form.rings
              .map((r) => ({
                distance_ft: lenFt(r.distance),
                boxes_per_side: num(r.boxes_per_side),
              }))
              .filter((r) => r.distance_ft != null)
          : undefined,
    },
  };
  const sources: Record<string, string> = {};
  for (const [k, v] of Object.entries(form.sources)) {
    if (v.trim()) sources[k] = v.trim();
  }
  if (Object.keys(sources).length) advanced.sources = sources;
  return advanced;
}

function noticesFor(prefix: string, notices: Notice[]) {
  return notices.filter(
    (n) => n.field === prefix || n.field.startsWith(prefix + ".") || n.field.startsWith(prefix + "["),
  );
}

function NoticeList({ items }: { items: Notice[] }) {
  if (!items.length) return null;
  return (
    <ul className="notices">
      {items.map((n, i) => (
        <li key={i}>{n.message}</li>
      ))}
    </ul>
  );
}

export default function AdvancedPanels({
  form,
  setForm,
  notices,
  sourceKeys,
  units,
}: {
  form: AdvFormState;
  setForm: (f: AdvFormState) => void;
  notices: Notice[];
  sourceKeys: string[];
  units: Units;
}) {
  const patch = (p: Partial<AdvFormState>) => setForm({ ...form, ...p });
  const unit = units;
  const subMin = fromFeet(5, units);
  const subMax = fromFeet(8, units);
  const subStep = units === "m" ? 0.05 : 0.1;
  const defaultRingDistance = formatLenFromFt(250, units);

  return (
    <div className="adv-panels">
      <details className="adv-sec" open>
        <summary>Mains</summary>
        <div className="field">
          <label htmlFor="mains-spread">L/R spread (centre-to-centre)</label>
          <div className="input-row">
            <input
              id="mains-spread"
              type="number"
              value={form.mainsSpread}
              onChange={(e) => patch({ mainsSpread: e.target.value })}
              step={units === "m" ? 0.1 : 1}
            />
            <span className="unit">{unit}</span>
          </div>
        </div>
        <div className="field">
          <label htmlFor="mains-boxes">Boxes per side</label>
          <input
            id="mains-boxes"
            type="number"
            value={form.mainsBoxes}
            onChange={(e) => patch({ mainsBoxes: e.target.value })}
            min={6}
            max={24}
          />
          <div className="hint">Frame angle, splay and trim stay engine-derived.</div>
        </div>
        <NoticeList items={noticesFor("mains", notices)} />
      </details>

      <details className="adv-sec">
        <summary>Subs</summary>
        <div className="field">
          <label htmlFor="sub-stacks">Stack count</label>
          <input
            id="sub-stacks"
            type="number"
            value={form.subStacks}
            onChange={(e) => patch({ subStacks: e.target.value })}
            min={3}
            max={14}
          />
        </div>
        <div className="field">
          <label htmlFor="sub-spacing">Spacing (c-c)</label>
          <div className="input-row">
            <input
              id="sub-spacing"
              type="number"
              value={form.subSpacing}
              onChange={(e) => patch({ subSpacing: e.target.value })}
              min={subMin}
              max={subMax}
              step={subStep}
            />
            <span className="unit">{unit}</span>
          </div>
        </div>
        <NoticeList items={noticesFor("subs", notices)} />
      </details>

      <details className="adv-sec">
        <summary>Out fills</summary>
        <div className="field">
          <label className="check">
            <input
              type="checkbox"
              checked={form.outEnabled}
              onChange={(e) => patch({ outEnabled: e.target.checked })}
            />
            Enabled
          </label>
        </div>
        {form.outEnabled && (
          <div className="field">
            <label htmlFor="out-boxes">Boxes per side</label>
            <input
              id="out-boxes"
              type="number"
              value={form.outBoxes}
              onChange={(e) => patch({ outBoxes: e.target.value })}
              min={4}
              max={16}
            />
          </div>
        )}
        <NoticeList items={noticesFor("out_fills", notices)} />
      </details>

      <details className="adv-sec">
        <summary>Front fills</summary>
        <div className="field">
          <label className="check">
            <input
              type="checkbox"
              checked={form.ffEnabled}
              onChange={(e) => patch({ ffEnabled: e.target.checked })}
            />
            Enabled
          </label>
        </div>
        {form.ffEnabled && (
          <div className="field">
            <label htmlFor="ff-count">Count (even)</label>
            <input
              id="ff-count"
              type="number"
              value={form.ffCount}
              onChange={(e) => patch({ ffCount: e.target.value })}
              min={4}
              max={12}
              step={2}
            />
          </div>
        )}
        <NoticeList items={noticesFor("front_fills", notices)} />
      </details>

      <details className="adv-sec">
        <summary>Delays</summary>
        <div className="field">
          <label>Mode</label>
          <div className="seg">
            <button
              type="button"
              className={form.delayMode === "auto" ? "on" : ""}
              onClick={() => patch({ delayMode: "auto" })}
            >
              Auto
            </button>
            <button
              type="button"
              className={form.delayMode === "manual" ? "on" : ""}
              onClick={() =>
                patch({
                  delayMode: "manual",
                  rings:
                    form.rings.length > 0
                      ? form.rings
                      : [{ distance: defaultRingDistance, boxes_per_side: "8" }],
                })
              }
            >
              Manual
            </button>
          </div>
        </div>
        {form.delayMode === "manual" && (
          <div className="ring-list">
            {form.rings.map((ring, i) => (
              <div className="ring-row" key={i}>
                <div className="field">
                  <label>Ring {i + 1} distance</label>
                  <div className="input-row">
                    <input
                      type="number"
                      value={ring.distance}
                      onChange={(e) => {
                        const rings = form.rings.slice();
                        rings[i] = { ...ring, distance: e.target.value };
                        patch({ rings });
                      }}
                      step={units === "m" ? 0.1 : 1}
                    />
                    <span className="unit">{unit}</span>
                  </div>
                </div>
                <div className="field">
                  <label>Boxes / side</label>
                  <input
                    type="number"
                    value={ring.boxes_per_side}
                    onChange={(e) => {
                      const rings = form.rings.slice();
                      rings[i] = { ...ring, boxes_per_side: e.target.value };
                      patch({ rings });
                    }}
                    min={4}
                    max={16}
                  />
                </div>
                <button
                  type="button"
                  className="btn-ghost ring-remove"
                  onClick={() => patch({ rings: form.rings.filter((_, j) => j !== i) })}
                  disabled={form.rings.length <= 1}
                >
                  Remove
                </button>
              </div>
            ))}
            {form.rings.length < 4 && (
              <button
                type="button"
                className="btn-ghost"
                onClick={() =>
                  patch({
                    rings: [
                      ...form.rings,
                      { distance: "", boxes_per_side: "8" },
                    ],
                  })
                }
              >
                + Add ring
              </button>
            )}
          </div>
        )}
        <NoticeList items={notices.filter((n) => n.field.startsWith("delays"))} />
      </details>

      <details className="adv-sec">
        <summary>Sources</summary>
        <div className="hint" style={{ marginBottom: 10 }}>
          Label-only overrides (shown on cards). Deep input routing is out of scope.
        </div>
        {(sourceKeys.length ? sourceKeys : ["Mains", "Sub Array", "Front Fills", "Out Fills"]).map(
          (key) => (
            <div className="field" key={key}>
              <label htmlFor={`src-${key}`}>{key}</label>
              <input
                id={`src-${key}`}
                type="text"
                value={form.sources[key] ?? ""}
                placeholder={key}
                onChange={(e) =>
                  patch({ sources: { ...form.sources, [key]: e.target.value } })
                }
              />
            </div>
          ),
        )}
      </details>
    </div>
  );
}
