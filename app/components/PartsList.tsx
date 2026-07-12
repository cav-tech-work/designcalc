"use client";

import { Design, PartLine } from "@/lib/types";

function toCsv(parts: PartLine[]): string {
  const header = "Category,Item,Quantity";
  const rows = parts.map((p) => `${p.category},${p.item},${p.qty}`);
  return [header, ...rows].join("\n");
}

export default function PartsList({ design }: { design: Design }) {
  const parts = design.parts;

  const downloadCsv = () => {
    const blob = new Blob([toCsv(parts)], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `DesignCalc_parts_${design.venue.depth_ft}x${design.venue.width_ft}ft.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // group by category, preserving order of first appearance
  const cats: string[] = [];
  for (const p of parts) if (!cats.includes(p.category)) cats.push(p.category);

  return (
    <div className="panel">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
        <h2 style={{ margin: 0 }}>Parts list</h2>
        <button className="btn-ghost" onClick={downloadCsv}>
          Download CSV
        </button>
      </div>
      <table className="parts">
        <thead>
          <tr>
            <th>Category</th>
            <th>Item</th>
            <th style={{ textAlign: "right" }}>Qty</th>
          </tr>
        </thead>
        <tbody>
          {cats.map((cat) =>
            parts
              .filter((p) => p.category === cat)
              .map((p, i) => (
                <tr key={`${cat}-${p.item}`}>
                  <td className="cat-tag">{i === 0 ? cat : ""}</td>
                  <td>{p.item}</td>
                  <td className="qty">{p.qty}</td>
                </tr>
              ))
          )}
        </tbody>
      </table>
    </div>
  );
}
