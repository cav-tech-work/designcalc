"use client";

import { Design, Subsystem } from "@/lib/types";
import { roleColor } from "@/lib/palette";

/**
 * Top-down plan of the flat-ground design.
 *
 * Layout convention (like a real PA plot):
 *   ┌ stage bar ┐
 *   │ downstage band │  ← near-stage systems (mains, subs, fills, out fills).
 *   │                │    They all sit within ~2 m of the stage, so they are laid out
 *   │                │    in a FIXED band (not to depth-scale) to stay readable.
 *   │ audience field │  ← to scale by depth; delay towers placed at true distance.
 *   └────────────────┘
 * Lateral (width) is to scale everywhere, so columns line up.
 */
export default function PlanPreview({ design }: { design: Design }) {
  const { venue, subsystems } = design;

  const W = 720;
  const H = 560;
  const leftPad = 46;
  const rightPad = 22;

  // lateral (width) scale — shared by band and field so columns align
  const rectLeft = leftPad;
  const rectRight = W - rightPad;
  const cx = (rectLeft + rectRight) / 2;
  const sx = (rectRight - rectLeft) / (venue.width_m || 1);
  const X = (lateral_m: number) => cx - lateral_m * sx;

  // vertical zones
  const stageY = 20;
  const stageH = 13;
  const bandTop = 52;
  const bandBottom = 188;
  const fieldTop = 202;
  const fieldBottom = 524;

  const totalDepth = venue.front_offset_m + venue.depth_m;
  const yField = (depth_m: number) => {
    const span = totalDepth - venue.front_offset_m || 1;
    const f = Math.max(0, Math.min(1, (depth_m - venue.front_offset_m) / span));
    return fieldTop + f * (fieldBottom - fieldTop);
  };

  // split systems: near-stage (band) vs field (delays / anything deep)
  const NEAR_M = 20;
  const near = subsystems.filter((s) => s.position.depth_m < NEAR_M);
  const field = subsystems.filter((s) => s.position.depth_m >= NEAR_M);

  const subGrp = near.filter((s) => s.role.toLowerCase().startsWith("sub"));
  const frontGrp = near.filter((s) => s.role.toLowerCase().startsWith("front"));
  const hangGrp = near.filter((s) => {
    const r = s.role.toLowerCase();
    return r.startsWith("main") || r.startsWith("out");
  });

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      style={{ display: "block", background: "#0d0d0f", borderRadius: 8, border: "1px solid #1b1b1e" }}
      role="img"
      aria-label="Top-down plan of the sound system design"
    >
      {/* audience field rectangle */}
      <rect x={rectLeft} y={fieldTop} width={rectRight - rectLeft} height={fieldBottom - fieldTop} fill="#111214" stroke="#26262a" strokeWidth={1} rx={3} />
      <line x1={cx} y1={fieldTop} x2={cx} y2={fieldBottom} stroke="#1c1c20" strokeWidth={1} strokeDasharray="3 6" />

      {/* stage bar */}
      <rect x={cx - 90} y={stageY} width={180} height={stageH} fill="#1b1b1e" stroke="#2a2a2f" strokeWidth={1} rx={2} />
      <text x={cx} y={stageY + 9} textAnchor="middle" fontSize={9} fill="#7a7a82" letterSpacing="2">
        STAGE
      </text>

      {/* downstage divider + caption */}
      <line x1={rectLeft} y1={bandBottom} x2={rectRight} y2={bandBottom} stroke="#26262a" strokeWidth={1} strokeDasharray="2 4" />
      <text x={rectLeft} y={bandBottom - 6} fontSize={8} fill="#5a5a62" letterSpacing="0.5">
        downstage — near-stage detail, not to scale
      </text>

      {/* depth ticks on the field */}
      {[0.25, 0.5, 0.75, 1].map((f) => {
        const dm = venue.front_offset_m + (totalDepth - venue.front_offset_m) * f;
        const yy = yField(dm);
        const ft = Math.round(dm / 0.3048);
        return (
          <g key={f}>
            <line x1={rectLeft - 6} y1={yy} x2={rectLeft} y2={yy} stroke="#3a3a40" strokeWidth={1} />
            <text x={rectLeft - 9} y={yy + 3} textAnchor="end" fontSize={8.5} fill="#6c6c74">
              {ft}&#39;
            </text>
          </g>
        );
      })}
      <text x={cx} y={fieldBottom + 18} textAnchor="middle" fontSize={9.5} fill="#6c6c74">
        {venue.width_ft}&#39; wide &middot; {venue.depth_ft}&#39; deep
      </text>

      {/* --- downstage band --- */}
      {/* mains + out fills: vertical hangs at true lateral */}
      {hangGrp.map((s) => (
        <Hang key={s.id} sub={s} x={X(s.position.lateral_m)} topY={72} labelAbove maxBoxes={16} bh={3.6} />
      ))}

      {/* sub array: wide centred bar */}
      {subGrp.map((s) => {
        const w = Math.max(70, Math.min(rectRight - rectLeft - 40, s.box_count * 6));
        const y = 84;
        return (
          <g key={s.id}>
            <text x={X(s.position.lateral_m)} y={y - 9} textAnchor="middle" fontSize={9} fill={roleColor(s.role, s.box_model)} fontWeight={600}>
              {s.label}
            </text>
            <rect x={X(s.position.lateral_m) - w / 2} y={y} width={w} height={8} rx={2} fill={roleColor(s.role, s.box_model)} opacity={0.9} />
            <text x={X(s.position.lateral_m)} y={y + 20} textAnchor="middle" fontSize={8} fill="#8a8a92">
              {s.box_model} &times;{s.box_count}
            </text>
          </g>
        );
      })}

      {/* front fills: small centred cluster below the subs */}
      {frontGrp.map((s) => {
        const y = 138;
        const x = X(s.position.lateral_m);
        return (
          <g key={s.id}>
            <rect x={x - 5} y={y - 5} width={10} height={10} rx={2} transform={`rotate(45 ${x} ${y})`} fill={roleColor(s.role, s.box_model)} />
            <text x={x} y={y + 20} textAnchor="middle" fontSize={9} fill={roleColor(s.role, s.box_model)} fontWeight={600}>
              {s.label}
            </text>
            <text x={x} y={y + 31} textAnchor="middle" fontSize={8} fill="#8a8a92">
              {s.box_model} &times;{s.box_count}
            </text>
          </g>
        );
      })}

      {/* --- field: delay towers at true depth --- */}
      {field.map((s) => (
        <Hang
          key={s.id}
          sub={s}
          x={X(s.position.lateral_m)}
          topY={yField(s.position.depth_m) - 18}
          labelAbove
          maxBoxes={10}
          bh={3.0}
        />
      ))}
    </svg>
  );
}

function Hang({
  sub,
  x,
  topY,
  labelAbove,
  maxBoxes,
  bh,
}: {
  sub: Subsystem;
  x: number;
  topY: number;
  labelAbove: boolean;
  maxBoxes: number;
  bh: number;
}) {
  const color = roleColor(sub.role, sub.box_model);
  const n = Math.min(sub.box_count, maxBoxes);
  const bw = 11;
  const gap = 0.7;
  const height = n * (bh + gap);

  return (
    <g>
      {labelAbove && (
        <text x={x} y={topY - 6} textAnchor="middle" fontSize={9} fill={color} fontWeight={600}>
          {sub.label}
        </text>
      )}
      {Array.from({ length: n }).map((_, i) => (
        <rect key={i} x={x - bw / 2} y={topY + i * (bh + gap)} width={bw} height={bh} rx={0.8} fill={color} opacity={0.92} />
      ))}
      <text x={x} y={topY + height + 10} textAnchor="middle" fontSize={8} fill="#8a8a92">
        {sub.box_model} &times;{sub.box_count}
      </text>
    </g>
  );
}
