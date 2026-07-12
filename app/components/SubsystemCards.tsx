"use client";

import { Design } from "@/lib/types";
import { roleColor } from "@/lib/palette";

export default function SubsystemCards({ design }: { design: Design }) {
  return (
    <div className="cards">
      {design.subsystems.map((sub) => {
        const color = roleColor(sub.role, sub.box_model);
        return (
          <div className="card" key={sub.id}>
            <div className="role">
              <span className="swatch" style={{ background: color }} />
              {sub.label}
            </div>
            <div className="model">
              {sub.box_model} &middot; {sub.box_count} {sub.box_count === 1 ? "box" : "boxes"}
            </div>

            <div className="stat">
              <span className="k">Depth</span>
              <span className="v">{sub.position.depth_ft}&#39;</span>
            </div>
            <div className="stat">
              <span className="k">Lateral</span>
              <span className="v">
                {sub.position.lateral_ft === 0 ? "centre" : `${Math.abs(sub.position.lateral_ft)}' ${sub.side}`}
              </span>
            </div>
            {sub.lowest_edge_ft != null && (
              <div className="stat">
                <span className="k">Lowest edge</span>
                <span className="v">{sub.lowest_edge_ft}&#39;</span>
              </div>
            )}
            {sub.aim_deg != null && (
              <div className="stat">
                <span className="k">Aim</span>
                <span className="v">{sub.aim_deg}&deg;</span>
              </div>
            )}
            <div className="stat">
              <span className="k">Source</span>
              <span className="v">{sub.source_label}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
