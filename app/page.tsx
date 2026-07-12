"use client";

import { useEffect, useMemo, useState } from "react";
import {
  GenerateResponse,
  ApiError,
  Units,
  Notice,
} from "@/lib/types";
import { computeAutoDefaults, toFeet } from "@/lib/defaults";
import PlanPreview from "./components/PlanPreview";
import SubsystemCards from "./components/SubsystemCards";
import PartsList from "./components/PartsList";
import AdvancedPanels, {
  AdvFormState,
  defaultsToForm,
  effectiveToForm,
  formToAdvanced,
} from "./components/AdvancedPanels";

type Mode = "simple" | "advanced";

function downloadDbpr(base64: string, filename: string) {
  const bytes = atob(base64);
  const arr = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
  const blob = new Blob([arr], { type: "application/octet-stream" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function Home() {
  const [mode, setMode] = useState<Mode>("simple");
  const [width, setWidth] = useState("220");
  const [depth, setDepth] = useState("450");
  const [units, setUnits] = useState<Units>("ft");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [adv, setAdv] = useState<AdvFormState>(() =>
    defaultsToForm(computeAutoDefaults(220, 450)),
  );

  const widthFt = toFeet(parseFloat(width) || 220, units);
  const depthFt = toFeet(parseFloat(depth) || 450, units);

  // Prefill advanced fields from auto-defaults when venue size changes (and no result yet).
  useEffect(() => {
    if (mode !== "advanced") return;
    if (result) return;
    setAdv(defaultsToForm(computeAutoDefaults(widthFt, depthFt)));
  }, [mode, widthFt, depthFt, result]);

  const sourceKeys = useMemo(() => {
    if (!result) return ["Mains", "Sub Array", "Front Fills", "Out Fills"];
    const roles = Array.from(new Set(result.design.subsystems.map((s) => s.role)));
    return roles;
  }, [result]);

  const generate = async () => {
    setErrors([]);
    const w = parseFloat(width);
    const d = parseFloat(depth);
    if (isNaN(w) || isNaN(d)) {
      setErrors(["Please enter numeric width and depth."]);
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const body: Record<string, unknown> = { width_ft: w, depth_ft: d, units };
      if (mode === "advanced") {
        body.advanced = formToAdvanced(adv);
      }
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) {
        const err = data as ApiError;
        setErrors(err.messages ?? [err.message ?? "Something went wrong."]);
        return;
      }
      const ok = data as GenerateResponse;
      setResult(ok);
      setNotices(ok.notices ?? []);
      if (mode === "advanced" && ok.effective) {
        setAdv((prev) => effectiveToForm(ok.effective, prev));
      }
    } catch {
      setErrors(["Could not reach the design engine. Please try again."]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="topbar">
        <div className="wrap row">
          <div className="brand">
            <span className="mark">
              Design<span className="dot">Calc</span>
            </span>
            <span className="tag">flat-ground system designer</span>
          </div>
          <span className="meta">outputs ArrayCalc .dbpr</span>
        </div>
      </div>

      <div className="wrap">
        <div className="hero">
          <div className="kicker">{mode === "simple" ? "Simple mode" : "Advanced mode"}</div>
          <h1>Describe the field. Get a system.</h1>
          <p>
            Enter a flat, rectangular venue&rsquo;s dimensions and DesignCalc lays out a complete
            house-style d&amp;b system &mdash; mains, subs, fills and delays &mdash; as a top-down plan
            and a valid ArrayCalc <code>.dbpr</code> you can open and refine.
            {mode === "advanced" && (
              <> Override spread, counts, delays and labels; risky acoustics stay engine-derived.</>
            )}
          </p>
        </div>

        <div className="grid">
          {/* --- input panel --- */}
          <div className="panel">
            <h2>Venue</h2>

            <div className="field">
              <label>Mode</label>
              <div className="seg">
                <button
                  type="button"
                  className={mode === "simple" ? "on" : ""}
                  onClick={() => {
                    setMode("simple");
                    setNotices([]);
                  }}
                >
                  Simple
                </button>
                <button
                  type="button"
                  className={mode === "advanced" ? "on" : ""}
                  onClick={() => setMode("advanced")}
                >
                  Advanced
                </button>
              </div>
            </div>

            <div className="field">
              <label htmlFor="width">Width</label>
              <div className="input-row">
                <input
                  id="width"
                  type="number"
                  value={width}
                  onChange={(e) => setWidth(e.target.value)}
                  min={30}
                  onKeyDown={(e) => e.key === "Enter" && generate()}
                />
                <span className="unit">{units}</span>
              </div>
              <div className="hint">Audience-area width, side to side.</div>
            </div>

            <div className="field">
              <label htmlFor="depth">Depth</label>
              <div className="input-row">
                <input
                  id="depth"
                  type="number"
                  value={depth}
                  onChange={(e) => setDepth(e.target.value)}
                  min={30}
                  onKeyDown={(e) => e.key === "Enter" && generate()}
                />
                <span className="unit">{units}</span>
              </div>
              <div className="hint">Stage to the back of the audience.</div>
            </div>

            <div className="field">
              <label>Units</label>
              <div className="seg">
                <button className={units === "ft" ? "on" : ""} onClick={() => setUnits("ft")}>
                  Feet
                </button>
                <button className={units === "m" ? "on" : ""} onClick={() => setUnits("m")}>
                  Metres
                </button>
              </div>
            </div>

            {mode === "advanced" && (
              <AdvancedPanels
                form={adv}
                setForm={setAdv}
                notices={notices}
                sourceKeys={sourceKeys}
              />
            )}

            {errors.length > 0 && (
              <ul className="errors" style={{ listStyle: "none", padding: "12px 14px", margin: "0 0 16px" }}>
                {errors.map((e, i) => (
                  <li key={i}>{e}</li>
                ))}
              </ul>
            )}

            <button className="btn" onClick={generate} disabled={loading}>
              {loading ? "Generating…" : "Generate design"}
            </button>
          </div>

          {/* --- output panel --- */}
          <div>
            {loading && (
              <div className="loading">
                <span className="spinner" />
                Laying out arrays, subs, fills and delays&hellip;
              </div>
            )}

            {!loading && !result && (
              <div className="panel">
                <div className="empty">
                  Enter a venue width and depth, then <strong>Generate design</strong>.
                  <br />
                  Your plan, subsystem breakdown, parts list and <code>.dbpr</code> download appear here.
                </div>
              </div>
            )}

            {!loading && result && (
              <div className="results">
                <div className="result-head">
                  <div>
                    <div className="title">
                      {result.design.venue.depth_ft}&#39; &times; {result.design.venue.width_ft}&#39; flat ground
                    </div>
                    <div className="sub">
                      {result.design.subsystems.length} subsystems &middot;{" "}
                      {result.design.parts
                        .filter((p) => p.category === "Loudspeakers")
                        .reduce((n, p) => n + p.qty, 0)}{" "}
                      loudspeakers &middot; file integrity: {result.meta.integrity}
                      {result.notices?.length ? (
                        <> &middot; {result.notices.length} clamp notice{result.notices.length > 1 ? "s" : ""}</>
                      ) : null}
                    </div>
                  </div>
                  <div className="dl-row">
                    <button className="btn-ghost" onClick={() => downloadDbpr(result.dbpr_base64, result.filename)}>
                      &#8595; Download .dbpr
                    </button>
                  </div>
                </div>

                {result.notices?.length > 0 && (
                  <ul className="notices notices-banner">
                    {result.notices.map((n, i) => (
                      <li key={i}>{n.message}</li>
                    ))}
                  </ul>
                )}

                <PlanPreview design={result.design} />

                <div className="panel">
                  <h2>Design notes</h2>
                  <div className="notes">
                    <div className="note">
                      <div className="k">Frame angle</div>
                      <div className="v">{result.meta.frame_angle}&deg;</div>
                    </div>
                    <div className="note">
                      <div className="k">Lowest edge</div>
                      <div className="v">{result.meta.lowest_edge_ft}&#39;</div>
                    </div>
                    <div className="note">
                      <div className="k">Mains reach</div>
                      <div className="v">{Math.round(result.meta.mains_coverage_end_m / 0.3048)}&#39;</div>
                    </div>
                    <div className="note">
                      <div className="k">Out fills</div>
                      <div className="v">{result.meta.out_fills ? "Yes" : "No"}</div>
                    </div>
                    {result.meta.delay_rings.map((ring) => (
                      <div className="note" key={ring.ring}>
                        <div className="k">Delay {ring.ring}</div>
                        <div className="v">{ring.delay_ms} ms</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h2 style={{ fontSize: 13, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--muted)", marginBottom: 14 }}>
                    Subsystems
                  </h2>
                  <SubsystemCards design={result.design} />
                </div>

                <PartsList design={result.design} />
              </div>
            )}
          </div>
        </div>

        <div className="footer">
          <div className="disc">
            DesignCalc produces a house-style starting design for flat, rectangular open-ground venues.
            ArrayCalc remains the authority for acoustic prediction and rigging safety &mdash; always verify
            the generated project before deployment.
          </div>
        </div>
      </div>
    </>
  );
}
