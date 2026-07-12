// Colour per box model / role — used by both the plan preview and the cards
// so a symbol on the drawing always matches its card.

export function roleColor(role: string, model: string): string {
  const r = role.toLowerCase();
  if (r.startsWith("main")) return "#e2001a";      // d&b red — the mains
  if (r.startsWith("sub")) return "#f0f0f2";       // white — subs
  if (r.startsWith("front")) return "#35c46a";     // green — front fills
  if (r.startsWith("out")) return "#e5a300";       // amber — out fills
  if (r.startsWith("delay")) return "#4aa3ff";     // blue — delays
  // fallback by model
  if (model === "SL-SUB") return "#f0f0f2";
  return "#9a9aa2";
}
