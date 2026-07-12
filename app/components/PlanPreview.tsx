"use client";

import { Design, Subsystem } from "@/lib/types";
import { roleColor } from "@/lib/palette";

/**
 * Top-down (bird's-eye) plan of the flat-ground design.
 * Vertical axis = depth away from the stage (stage at top).
 * Horizontal axis = lateral width (centre = 0).
 * Rendered to scale as SVG.
 */
export default function PlanPreview({ design }: { design: Design }) {
  const { venue, subsystems } = design;

  // world extents (metres)
  const halfW = venue.width_m / 2;
  const totalDepth = venue.front_offset_m + venue.depth_m; // stage (0) -> back of audience

  // svg canvas
  const W = 720;
  const H = 560;
  const pad = 46;

  // scale world -> screen, keeping aspect ratio
  const sx = (W - pad * 2) / (venue.width_m || 1);
  const sy = (H - pad * 2) / (totalDepth || 1);
  const s = Math.min(sx, sy);

  const cx = W / 2; // lateral centre on screen
  // map: lateral(+L) -> screen x ; depth -> screen y (top = stage)
  const X = (lateral_m: number) => cx - lateral_m * s; // +L to the left of screen
  const Y = (depth_m: number) => pad + depth_m * s;

  const venueLeft = X(halfW);
  const venueRight = X(-halfW);
  const venueTop = Y(venue.front_offset_m);
  const venueBottom = Y(totalDepth);

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      style={{ display: "block", background: "#0d0d0f", borderRadius: 8, border: "1px solid #1b1b1e" }}
      role="img"
      aria-label="Top-down plan of the sound system design"
    >
      {/* audience area */}
      <rect
        x={venueLeft}
        y={venueTop}
        width={venueRight - venueLeft}
        height={venueBottom - venueTop}
        fill="#111214"
        stroke="#2a2a2f"
        strokeWidth={1}
        rx={3}
      />
      {/* centre line */}
      <line x1={cx} y1={venueTop} x2={cx} y2={venueBottom} stroke="#1f1f23" strokeWidth={1} strokeDasharray="3 5" />

      {/* stage bar */}
      <rect x={venueLeft} y={pad - 16} width={venueRight - venueLeft} height={16} fill="#1b1b1e" stroke="#2a2a2f" strokeWidth={1} rx={2} />
      <text x={cx} y={pad - 4} textAnchor="middle" fontSize={9.5} fill="#6c6c74" letterSpacing="1.5">
        STAGE
      </text>

      {/* depth scale ticks (every ~1/4) */}
      {[0.25, 0.5, 0.75, 1].map((f) => {
        const dm = totalDepth * f;
        const yy = Y(dm);
        const ft = Math.round(dm / 0.3048);
        return (
          <g key={f}>
            <line x1={venueLeft - 6} y1={yy} x2={venueLeft} y2={yy} stroke="#3a3a40" strokeWidth={1} />
            <text x={venueLeft - 9} y={yy + 3} textAnchor="end" fontSize={8.5} fill="#6c6c74">
              {ft}&#39;
            </text>
          </g>
        );
      })}

      {/* width label */}
      <text x={cx} y={venueBottom + 18} textAnchor="middle" fontSize={9.5} fill="#6c6c74">
        {venue.width_ft}&#39; wide &middot; {venue.depth_ft}&#39; deep
      </text>

      {/* subsystems */}
      {subsystems.map((sub) => (
        <SubSymbol key={sub.id} sub={sub} X={X} Y={Y} s={s} />
      ))}
    </svg>
  );
}

function SubSymbol({
  sub,
  X,
  Y,
  s,
}: {
  sub: Subsystem;
  X: (m: number) => number;
  Y: (m: number) => number;
  s: number;
}) {
  const color = roleColor(sub.role, sub.box_model);
  const x = X(sub.position.lateral_m);
  const y = Y(sub.position.depth_m);
  const r = sub.role.toLowerCase();

  // shape by role
  let shape;
  if (r.startsWith("sub")) {
    // wide bar across the front
    const w = Math.max(60, Math.min(220, sub.box_count * 6));
    shape = <rect x={x - w / 2} y={y - 4} width={w} height={8} rx={2} fill={color} opacity={0.9} />;
  } else if (r.startsWith("main") || r.startsWith("delay") || r.startsWith("out")) {
    // line array hang — small vertical stack of boxes
    const n = Math.min(sub.box_count, 16);
    const bh = 3.2;
    const bw = 11;
    shape = (
      <g>
        {Array.from({ length: n }).map((_, i) => (
          <rect
            key={i}
            x={x - bw / 2}
            y={y + i * (bh + 0.6)}
            width={bw}
            height={bh}
            rx={0.8}
            fill={color}
            opacity={0.92}
          />
        ))}
      </g>
    );
  } else {
    // point-source fills — a small diamond cluster
    shape = <rect x={x - 5} y={y - 5} width={10} height={10} rx={2} transform={`rotate(45 ${x} ${y})`} fill={color} />;
  }

  const labelBelow = r.startsWith("sub") || r.startsWith("front");
  const ly = labelBelow ? y + 20 : y - 8;

  return (
    <g>
      {shape}
      <text x={x} y={ly} textAnchor="middle" fontSize={9} fill={color} fontWeight={600}>
        {sub.label}
      </text>
      <text x={x} y={ly + 10} textAnchor="middle" fontSize={8} fill="#8a8a92">
        {sub.box_model} &times;{sub.box_count}
      </text>
    </g>
  );
}
